import time
import dbus

import pywifi

wifi = pywifi.PyWiFi()


def scan(iface):
    retry = True
    if retry:
        try:
            iface.scan()
            retry = False
        except dbus.exceptions.DBusException:
            retry = True
    return iface.scan_results()

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
    Netmask='255.255.255.0'
    IP = "192.168.45.1"
    i = IP.rindex('.')
    ipparts=IP[0:i]
    import ipdb;ipdb.set_trace()
    s = 'ifconfig ' + wlan + ' up ' + IP + ' netmask ' + Netmask
    s = 'dnsmasq --dhcp-authoritative --interface=' + wlan + ' --dhcp-range=' + ipparts + '.20,' + ipparts +'.100,' + Netmask + ',4h'
    s = "ifconfig wlp3s0 down"
    s = "iwconfig wlp3s0 mode ad-hoc"
    s = "iwconfig wlp3s0 key tuxeatpi"
    s = "iwconfig wlp3s0 essid MyNet"
    s = "ifconfig wlp3s0 192.168.45.1/24"

#cells = get_networks()


create_hotspod()
#print(cells)
#connect('wlp3s0', 'AndroidAP', 3, 'totototo')
