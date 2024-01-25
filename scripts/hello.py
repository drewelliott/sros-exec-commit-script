from pysros.management import connect
import json, sys

c = connect()

def parse_config():
    config=[]
    for line in sys.stdin:
        config.append(line)
    _config = "".join(str(e) for e in config)
    pysros_config = c.convert('/', _config, source_format='json', destination_format='pysros')
    return pysros_config

def parse_cpm(cpm_state):
    for k,cpm_data in cpm_state.items():
        installed_cf = []
        for flash_slot,flash_data in cpm_data['flash'].items():
            if flash_data['oper-state'].data == 'ok':
                installed_cf.append('cf' + str(flash_slot))
    return set(installed_cf)


def parse_log_config(config, cpm_flash_state):
    try:
        file_config = config['configure']['log']['file']
    except:
        pass
    error_logs = []
    for name, data in file_config.items():
        if 'compact-flash-location' in data.keys():
            d = data['compact-flash-location']
            for k,v in d.items(): 
                cf = v.data
                if cf == 'cf3':
                    my_err = "log file " + name + ":: cf3:\ is not allowed to be used for logging output"
                    error_logs.append(my_err)
                elif cf not in cpm_flash_state:
                    my_err = "log file " + name + ":: There is no compact flash installed in " + cf
                    error_logs.append(my_err)
    return error_logs
    
            
def main():
    candidate = parse_config()
    cpm_state = c.running.get('/state/cpm')
    cpm_flash_state = parse_cpm(cpm_state)
    error_logs = parse_log_config(candidate, cpm_flash_state)
    if error_logs:
        print("==============\nCOMMIT BLOCKED\n==============")
        for err in error_logs:
            print(err)
    else:
        top_level_element = list(candidate.keys())[0]
        c.candidate.set("/"+top_level_element,candidate[top_level_element],commit=False)
        print(c.candidate.compare(output_format='md_cli'))
        c.candidate.commit()
    
if __name__ == '__main__':
    main()     