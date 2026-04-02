import requests
import base64

class OpenStackAPI:
    def __init__(self):
        self.auth_url = "https://cloud-identity.uitiot.vn/v3/auth/tokens"
        self.compute_url = "https://cloud-compute.uitiot.vn/v2.1"
        self.network_url = "https://cloud-network.uitiot.vn/v2.0"
        self.image_url = "https://cloud-image.uitiot.vn/v2"
        self.token = None

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
        # 1. Lấy danh sách các mạng nội bộ (Không phải external)
        nets = requests.get(f"{self.network_url}/networks?router:external=False", headers=self.get_headers()).json().get('networks', [])
        internal_net_ids = [n['id'] for n in nets]
        
        # 2. Lấy tất cả subnet và chỉ giữ lại những subnet thuộc mạng nội bộ
        subnets = requests.get(f"{self.network_url}/subnets", headers=self.get_headers()).json().get('subnets', [])
        return [s for s in subnets if s['network_id'] in internal_net_ids]

    def get_router_attached_subnets(self, router_id):
        # Lấy danh sách các cổng (ports) đang cắm vào Router này
        res = requests.get(f"{self.network_url}/ports?device_id={router_id}", headers=self.get_headers())
        ports = res.json().get('ports', [])
        subnet_ids = []
        for p in ports:
            # Chỉ lấy những cổng đóng vai trò là interface nối xuống mạng nội bộ
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
        if res.status_code >= 400:
            err_msg = res.json().get('NeutronError', {}).get('message', 'Unknown error when creating subnet')
            raise Exception(err_msg)
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
        
        # Bắt lỗi nếu OpenStack từ chối
        if res.status_code >= 400:
            err_msg = res.json().get('NeutronError', {}).get('message', 'Lỗi không xác định')
            raise Exception(err_msg)
            
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
        res = requests.put(f"{self.network_url}/routers/{router_id}/remove_router_interface", 
                           json=payload, headers=self.get_headers())
        if res.status_code >= 400:
            err_msg = res.json().get('NeutronError', {}).get('message', 'Loi khi go interface')
            raise Exception(err_msg)
        return res.json()
    def remove_router_interface(self, router_id, subnet_id):
        payload = {"subnet_id": subnet_id}
        res = requests.put(f"{self.network_url}/routers/{router_id}/remove_router_interface", json=payload, headers=self.get_headers())
        if res.status_code >= 400:
            err_msg = res.json().get('NeutronError', {}).get('message', 'Unknown error when removing interface')
            raise Exception(err_msg)
        return res.json()

    # --- DELETE (DELETE) ---
    def delete_network(self, net_id):
        res = requests.delete(f"{self.network_url}/networks/{net_id}", headers=self.get_headers())
        if res.status_code >= 400:
            err_msg = res.json().get('NeutronError', {}).get('message', 'Unknown error when deleting network')
            raise Exception(err_msg)

    def delete_subnet(self, subnet_id):
        res = requests.delete(f"{self.network_url}/subnets/{subnet_id}", headers=self.get_headers())
        if res.status_code >= 400:
            err_msg = res.json().get('NeutronError', {}).get('message', 'Unknown error when deleting subnet')
            raise Exception(err_msg)

    def delete_router(self, router_id):
        res = requests.delete(f"{self.network_url}/routers/{router_id}", headers=self.get_headers())
        if res.status_code >= 400:
            err_msg = res.json().get('NeutronError', {}).get('message', 'Unknown error when deleting router')
            raise Exception(err_msg)
        
    def delete_instance(self, server_id):
        res = requests.delete(f"{self.compute_url}/servers/{server_id}", headers=self.get_headers())
        if res.status_code >= 400:
            err_msg = res.json().get('badRequest', {}).get('message', 'Unknown error when deleting instance')
            raise Exception(err_msg)

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
        # Tim Port ID cua may ao
        ports_res = requests.get(f"{self.network_url}/ports?device_id={server_id}", headers=self.get_headers())
        ports = ports_res.json().get("ports", [])
        if ports:
            port_id = ports[0]['id']
            # Gan IP vao Port
            requests.put(f"{self.network_url}/floatingips/{fip_id}", json={"floatingip": {"port_id": port_id}}, headers=self.get_headers())
# --- CAC HAM CHI TIET MAY AO (INSTANCE DETAILS) ---
    def get_instance_interfaces(self, server_id):
        res = requests.get(f"{self.network_url}/ports?device_id={server_id}", headers=self.get_headers())
        return res.json().get('ports', [])

    def get_instance_log(self, server_id, length=35):
        payload = {"os-getConsoleOutput": {"length": length}}
        res = requests.post(f"{self.compute_url}/servers/{server_id}/action", json=payload, headers=self.get_headers())
        if res.status_code == 200:
            return res.json().get("output", "")
        return "Khong the lay log (May ao co the dang tat hoac chua khoi dong xong)."

    def get_instance_console(self, server_id):
        # Su dung noVNC console mac dinh cua OpenStack
        payload = {"os-getVNCConsole": {"type": "novnc"}}
        res = requests.post(f"{self.compute_url}/servers/{server_id}/action", json=payload, headers=self.get_headers())
        if res.status_code == 200:
            return res.json().get("console", {}).get("url", "Khong tim thay URL Console.")
        return "Loi: Khong the lay duong dan Console tu OpenStack."

    def get_instance_actions(self, server_id):
        res = requests.get(f"{self.compute_url}/servers/{server_id}/os-instance-actions", headers=self.get_headers())
        if res.status_code == 200:
            return res.json().get("instanceActions", [])
        return []
