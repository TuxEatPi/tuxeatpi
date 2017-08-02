import time
import dbus
import subprocess

import pywifi

wifi = pywifi.PyWiFi()


def scan():
    hotspot_command = "nmcli c up tuxeatpi"
    subprocess.Popen(hotspot_command.split())
    # Scan
    hotspot_command = "nmcli device wifi rescan"
    subprocess.Popen(hotspot_command.split())
    hotspot_command = "nmcli device wifi list"
    proc = subprocess.Popen(hotspot_command.split(), stdout=subprocess.PIPE)
    output, err = proc.communicate()
    # TODO err
    signals = []
    for line in output.splitlines()[1:]:
        data = [d for d in line[3:].split(" ") if d != ""]
        signals.append({"name": data[0],
                        "signal": data[5],
                        "security": data[r75],
                        })
    return signals

def get_networks():

    cells = {}
    for wf_if in wifi.interfaces():
        cells[wf_if.name()] = []
        cells[wf_if.name()].extend(scan(wf_if))

    return cells

def connect(if_name, ssid, key_mgmt, password=""):
    wf_if = None
    for tmp_wf_if in wifi.interfaces():
        if tmp_wf_if.name() == if_name:
            wf_if = tmp_wf_if
    if wf_if is None:
        raise Exception()

    keys_mgmt_list = [value for key, value in pywifi.const.__dict__.items() if key.startswith('AUTH_ALG_')]
    if key_mgmt not in keys_mgmt_list:
        raise Exception()

    if key_mgmt != pywifi.const.AUTH_ALG_OPEN and (password in [None, ""]):
        raise Exception()


    wf_if.disconnect()
    wf_if.remove_all_network_profiles()
    timeout = 60
    print(wf_if.status())
    while wf_if.status() not in [pywifi.const.IFACE_DISCONNECTED, pywifi.const.IFACE_INACTIVE]:
        time.sleep(1)
        print("waiting disconnect")
        timeout -= 1
        if timeout == 0:
            raise Exception()

    profile = {'ssid': ssid,
               'key_mgmt': key_mgmt,
               'psk': password}
    tmp_profile = wf_if.add_network_profile(profile)
    wf_if.connect(tmp_profile)
    timeout = 60
    while wf_if.status() != pywifi.const.IFACE_CONNECTED:
        time.sleep(1)
        print("waiting connect")
        timeout -= 1
        if timeout == 0:
            raise Exception()

def get_ip_address():
    pass
    

def create_hotspod():
    hotspot_command = "nmcli d"
    proc = subprocess.Popen(hotspot_command.split(),
                     stdout=subprocess.PIPE)
    output, err = proc.communicate()
    if err:
        raise BaseException(err)

    ifname = None
    for line in output.splitlines():
        if line.find(b" wifi") != -1:
            ifname = line.split(b" ", 1)[0]
    if ifname is None:
        raise BaseException("No wifi interface found")

#    s = 'ifconfig ' + wlan + ' up ' + IP + ' netmask ' + Netmask
#    s = 'dnsmasq --dhcp-authoritative --interface=' + wlan + ' --dhcp-range=' + ipparts + '.20,' + ipparts +'.100,' + Netmask + ',4h'
#    hotspot_command = "nmcli c add type wifi ifname {} ssid tuxeatpi mode ap con-name tuxeatpi autoconnect no mac 8C:70:5A:F2:63:00  ipv4.method shared".format(ifname)
    hotspot_command = "nmcli radio wifi off"
    subprocess.Popen(hotspot_command.split())

    hotspot_command = "nmcli radio wifi"
    proc = subprocess.Popen(hotspot_command.split(), stdout=subprocess.PIPE)
    output, _ = proc.communicate()
    while output.strip() != b'disabled':
        proc = subprocess.Popen(hotspot_command.split(), stdout=subprocess.PIPE)
        output, _ = proc.communicate()

    hotspot_command = "nmcli radio wifi on"
    subprocess.Popen(hotspot_command.split())

    hotspot_command = "nmcli radio wifi"
    proc = subprocess.Popen(hotspot_command.split(), stdout=subprocess.PIPE)
    output, _ = proc.communicate()
    while output.strip() != b'enabled':
        proc = subprocess.Popen(hotspot_command.split(), stdout=subprocess.PIPE)
        output, _ = proc.communicate()


    hotspot_command = "nmcli c show tuxeatpi"
    proc = subprocess.Popen(hotspot_command.split(), stdout=subprocess.PIPE)
    output, _ = proc.communicate()
    if output == b'':
        hotspot_command = "nmcli c add type wifi ifname {} ssid tuxeatpi mode ap con-name tuxeatpi autoconnect no ipv4.method shared".format(ifname)
        subprocess.Popen(hotspot_command.split())

        hotspot_command = "nmcli c show tuxeatpi"
        proc = subprocess.Popen(hotspot_command.split(), stdout=subprocess.PIPE)
        output, _ = proc.communicate()
        while output == b'':
            print("DD")
            proc = subprocess.Popen(hotspot_command.split(), stdout=subprocess.PIPE)
            output, _ = proc.communicate()

    import ipdb;ipdb.set_trace()




    hotspot_command = "nmcli c down tuxeatpi"
    subprocess.Popen(hotspot_command.split())
    hotspot_command = "nmcli radio wifi off"
    subprocess.Popen(hotspot_command.split())

#cells = get_networks()


create_hotspod()
#print(cells)
#connect('wlp3s0', 'AndroidAP', 3, 'totototo')
