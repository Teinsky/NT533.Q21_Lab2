import requests
import base64

class OpenStackAPI:
    def __init__(self):
        self.auth_url = "https://cloud-identity.uitiot.vn/v3/auth/tokens"
        self.compute_url = "https://cloud-compute.uitiot.vn/v2.1"
        self.network_url = "https://cloud-network.uitiot.vn/v2.0"
        self.image_url = "https://cloud-image.uitiot.vn/v2"
        self.token = None
        self.lb_base_url = "https://cloud-loadbalancer.uitiot.vn"
        
    def login(self, username, password, project_name):
        payload = {
            "auth": {
                "identity": {"methods": ["password"], "password": {"user": {"domain": {"id": "default"}, "name": username, "password": password}}},
                "scope": {"project": {"domain": {"id": "default"}, "name": project_name}}
            }
        }
        res = requests.post(self.auth_url, json=payload)
        if res.status_code == 201:
            self.token = res.headers.get('X-Subject-Token')
        
                    
            return True
        return False

    def get_headers(self):
        return {"X-Auth-Token": self.token, "Content-Type": "application/json"}
    
    def get_limits(self):
        res = requests.get(f"{self.compute_url}/limits", headers=self.get_headers())
        if res.status_code == 200:
            return res.json().get("limits", {}).get("absolute", {})
        return {}

    # --- LISTING (GET) ---
    def get_internal_subnets(self):
        nets = requests.get(f"{self.network_url}/networks?router:external=False", headers=self.get_headers()).json().get('networks', [])
        internal_net_ids = [n['id'] for n in nets]
        
        subnets = requests.get(f"{self.network_url}/subnets", headers=self.get_headers()).json().get('subnets', [])
        return [s for s in subnets if s['network_id'] in internal_net_ids]

    def get_router_attached_subnets(self, router_id):
        res = requests.get(f"{self.network_url}/ports?device_id={router_id}", headers=self.get_headers())
        ports = res.json().get('ports', [])
        subnet_ids = []
        for p in ports:
            if p.get('device_owner') == 'network:router_interface':
                for ip in p.get('fixed_ips', []):
                    subnet_ids.append(ip.get('subnet_id'))
        return subnet_ids
    
    def get_flavors(self):
        res = requests.get(f"{self.compute_url}/flavors/detail", headers=self.get_headers())
        return res.json().get('flavors', [])

    def get_images(self):
        res = requests.get(f"{self.image_url}/images", headers=self.get_headers())
        return res.json().get('images', [])

    def get_networks(self):
        res = requests.get(f"{self.network_url}/networks", headers=self.get_headers())
        return res.json().get('networks', [])
    
    def get_subnets(self):
        res = requests.get(f"{self.network_url}/subnets", headers=self.get_headers())
        return res.json().get('subnets', [])
    
    def get_subnets_by_network(self, net_id):
        res = requests.get(f"{self.network_url}/subnets?network_id={net_id}", headers=self.get_headers())
        return res.json().get('subnets', [])

    def get_ports_by_network(self, net_id):
        res = requests.get(f"{self.network_url}/ports?network_id={net_id}", headers=self.get_headers())
        return res.json().get('ports', [])
    
    def get_routers(self):
        res = requests.get(f"{self.network_url}/routers", headers=self.get_headers())
        return res.json().get('routers', [])
        
    def get_instances(self):
        res = requests.get(f"{self.compute_url}/servers/detail", headers=self.get_headers())
        return res.json().get('servers', [])

    def get_external_network(self):
        res = requests.get(f"{self.network_url}/networks?router:external=True", headers=self.get_headers())
        nets = res.json().get('networks', [])
        return nets[0]['id'] if nets else None

    # --- CREATE (POST) ---
    def create_network(self, name):
        payload = {"network": {"name": name, "admin_state_up": True}}
        res = requests.post(f"{self.network_url}/networks", json=payload, headers=self.get_headers())
        return res.json()

    def create_subnet(self, net_id, name, cidr):
        payload = {"subnet": {"network_id": net_id, "ip_version": 4, "cidr": cidr, "name": name}}
        res = requests.post(f"{self.network_url}/subnets", json=payload, headers=self.get_headers())
        if res.status_code >= 400: raise Exception(res.json().get('NeutronError', {}).get('message', 'Unknown error'))
        return res.json()

    def create_router(self, name):
        payload = {"router": {"name": name, "admin_state_up": True}}
        res = requests.post(f"{self.network_url}/routers", json=payload, headers=self.get_headers())
        return res.json()

    def set_router_gateway(self, router_id, ext_net_id):
        payload = {"router": {"external_gateway_info": {"network_id": ext_net_id}}}
        requests.put(f"{self.network_url}/routers/{router_id}", json=payload, headers=self.get_headers())

    def add_router_interface(self, router_id, subnet_id):
        payload = {"subnet_id": subnet_id}
        res = requests.put(f"{self.network_url}/routers/{router_id}/add_router_interface", json=payload, headers=self.get_headers())
        if res.status_code >= 400: raise Exception(res.json().get('NeutronError', {}).get('message', 'Lỗi không xác định'))
        return res.json()

    def create_instance(self, name, flavor_id, image_id, net_id, user_data):
        user_data_b64 = base64.b64encode(user_data.encode('utf-8')).decode('utf-8')
        payload = {
            "server": {
                "name": name,
                "flavorRef": flavor_id,
                "networks": [{"uuid": net_id}],
                "security_groups": [{"name": "default"}],
                "user_data": user_data_b64,
                "block_device_mapping_v2": [{
                    "boot_index": 0, "uuid": image_id, "source_type": "image",
                    "destination_type": "volume", "volume_size": 15, "delete_on_termination": True
                }]
            }
        }
        res = requests.post(f"{self.compute_url}/servers", json=payload, headers=self.get_headers())
        return res.json()

    def get_router_interfaces(self, router_id):
        res = requests.get(f"{self.network_url}/ports?device_id={router_id}", headers=self.get_headers())
        ports = res.json().get('ports', [])
        return [p for p in ports if p.get('device_owner') == 'network:router_interface']

    def remove_router_interface(self, router_id, subnet_id):
        payload = {"subnet_id": subnet_id}
        res = requests.put(f"{self.network_url}/routers/{router_id}/remove_router_interface", json=payload, headers=self.get_headers())
        if res.status_code >= 400: raise Exception(res.json().get('NeutronError', {}).get('message', 'Unknown error'))
        return res.json()

    # --- DELETE (DELETE) ---
    def delete_network(self, net_id):
        res = requests.delete(f"{self.network_url}/networks/{net_id}", headers=self.get_headers())
        if res.status_code >= 400: raise Exception('Lỗi xóa mạng')

    def delete_subnet(self, subnet_id):
        res = requests.delete(f"{self.network_url}/subnets/{subnet_id}", headers=self.get_headers())
        if res.status_code >= 400: raise Exception('Lỗi xóa subnet')

    def delete_router(self, router_id):
        res = requests.delete(f"{self.network_url}/routers/{router_id}", headers=self.get_headers())
        if res.status_code >= 400: raise Exception('Lỗi xóa router')
        
    def delete_instance(self, server_id):
        res = requests.delete(f"{self.compute_url}/servers/{server_id}", headers=self.get_headers())
        if res.status_code >= 400: raise Exception('Lỗi xóa máy ảo')

    # --- FLOATING IP (CAU 6) ---
    def get_floating_ips(self):
        res = requests.get(f"{self.network_url}/floatingips", headers=self.get_headers())
        return res.json().get('floatingips', [])

    def allocate_floating_ip(self):
        ext_net_id = self.get_external_network()
        payload = {"floatingip": {"floating_network_id": ext_net_id}}
        res = requests.post(f"{self.network_url}/floatingips", json=payload, headers=self.get_headers())
        return res.json().get("floatingip", {})

    def associate_floating_ip(self, server_id, fip_id):
        ports_res = requests.get(f"{self.network_url}/ports?device_id={server_id}", headers=self.get_headers())
        ports = ports_res.json().get("ports", [])
        if ports:
            port_id = ports[0]['id']
            requests.put(f"{self.network_url}/floatingips/{fip_id}", json={"floatingip": {"port_id": port_id}}, headers=self.get_headers())

    # --- CAC HAM CHI TIET MAY AO (INSTANCE DETAILS) ---
    def get_instance_interfaces(self, server_id):
        res = requests.get(f"{self.network_url}/ports?device_id={server_id}", headers=self.get_headers())
        return res.json().get('ports', [])

    def get_instance_log(self, server_id, length=35):
        payload = {"os-getConsoleOutput": {"length": length}}
        res = requests.post(f"{self.compute_url}/servers/{server_id}/action", json=payload, headers=self.get_headers())
        if res.status_code == 200: return res.json().get("output", "")
        return "Khong the lay log."

    def get_instance_console(self, server_id):
        payload = {"os-getVNCConsole": {"type": "novnc"}}
        res = requests.post(f"{self.compute_url}/servers/{server_id}/action", json=payload, headers=self.get_headers())
        if res.status_code == 200: return res.json().get("console", {}).get("url", "")
        return "Loi: Khong the lay duong dan Console."

    def get_instance_actions(self, server_id):
        res = requests.get(f"{self.compute_url}/servers/{server_id}/os-instance-actions", headers=self.get_headers())
        if res.status_code == 200: return res.json().get("instanceActions", [])
        return []

    # --- CAC HAM QUAN LY LOAD BALANCER (CAU 7 & 8) ---
    def get_loadbalancers(self):
        res = requests.get(f"{self.lb_base_url}/v2.0/lbaas/loadbalancers", headers=self.get_headers())
        return res.json().get('loadbalancers', [])

    def create_loadbalancer(self, name, subnet_id):
        payload = {"loadbalancer": {"name": name, "vip_subnet_id": subnet_id, "admin_state_up": True}}
        res = requests.post(f"{self.lb_base_url}/v2.0/lbaas/loadbalancers", json=payload, headers=self.get_headers())
        if res.status_code >= 400: raise Exception(res.json().get('NeutronError', {}).get('message', 'Loi tao LB'))
        return res.json().get('loadbalancer')

    def create_listener(self, lb_id, name):
        payload = {"listener": {"name": name, "loadbalancer_id": lb_id, "protocol": "HTTP", "protocol_port": 80}}
        res = requests.post(f"{self.lb_base_url}/v2.0/lbaas/listeners", json=payload, headers=self.get_headers())
        if res.status_code >= 400: raise Exception(res.json().get('NeutronError', {}).get('message', 'Loi tao Listener'))
        return res.json().get('listener')

    def create_pool(self, listener_id, name):
        payload = {"pool": {"name": name, "listener_id": listener_id, "lb_algorithm": "ROUND_ROBIN", "protocol": "HTTP"}}
        res = requests.post(f"{self.lb_base_url}/v2.0/lbaas/pools", json=payload, headers=self.get_headers())
        if res.status_code >= 400: raise Exception(res.json().get('NeutronError', {}).get('message', 'Loi tao Pool'))
        return res.json().get('pool')

    def get_pool_members(self, pool_id):
        res = requests.get(f"{self.lb_base_url}/v2.0/lbaas/pools/{pool_id}/members", headers=self.get_headers())
        return res.json().get('members', [])

    def add_pool_member(self, pool_id, subnet_id, ip_address):
        payload = {"member": {"address": ip_address, "protocol_port": 80, "subnet_id": subnet_id}}
        res = requests.post(f"{self.lb_base_url}/v2.0/lbaas/pools/{pool_id}/members", json=payload, headers=self.get_headers())
        if res.status_code >= 400: raise Exception(res.json().get('NeutronError', {}).get('message', 'Loi them Member'))
        return res.json().get('member')

    def remove_pool_member(self, pool_id, member_id):
        res = requests.delete(f"{self.lb_base_url}/v2.0/lbaas/pools/{pool_id}/members/{member_id}", headers=self.get_headers())
        if res.status_code >= 400: raise Exception('Loi xoa Member')