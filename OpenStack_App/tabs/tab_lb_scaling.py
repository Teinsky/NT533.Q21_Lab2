import customtkinter as ctk
import threading
import time
import requests

class LBScalingTab(ctk.CTkFrame):
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api
        
        ctk.CTkLabel(self, text="5. Load Balancer & Scaling (Câu 7 & 8)", font=("Roboto", 20, "bold")).pack(pady=10, anchor="w", padx=10)

        # --- KHU VUC 1: KHOI TAO LOAD BALANCER ---
        self.frame_lb = ctk.CTkFrame(self)
        self.frame_lb.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(self.frame_lb, text="Bước 1: Khởi tạo hệ thống Cân bằng tải", font=("Roboto", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=10, sticky="w", padx=10)
        
        self.combo_subnet = ctk.CTkComboBox(self.frame_lb, width=250, values=["Đang tải..."])
        self.combo_subnet.grid(row=1, column=0, padx=10, pady=10)
        
        ctk.CTkButton(self.frame_lb, text="Tạo Mới Load Balancer", command=self.init_lb_system).grid(row=1, column=1, padx=10)
        self.lbl_lb_status = ctk.CTkLabel(self.frame_lb, text="", text_color="orange", wraplength=600)
        self.lbl_lb_status.grid(row=2, column=0, columnspan=3, sticky="w", padx=10)

        # --- KHU VUC 2: SCALING (TĂNG/GIẢM NODE) ---
        self.frame_scale = ctk.CTkFrame(self)
        self.frame_scale.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(self.frame_scale, text="Bước 2: Scale Tự động (Thêm/Bớt Web Node)", font=("Roboto", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=10, sticky="w", padx=10)

        ctk.CTkButton(self.frame_scale, text="+ SCALE UP (Tạo VM & Gắn LB)", fg_color="#27ae60", hover_color="#2ecc71", command=self.scale_up).grid(row=1, column=0, padx=10, pady=10)
        ctk.CTkButton(self.frame_scale, text="- SCALE DOWN (Xóa 1 Node)", fg_color="#c0392b", hover_color="#e74c3c", command=self.scale_down).grid(row=1, column=1, padx=10, pady=10)
        
        self.lbl_scale_status = ctk.CTkLabel(self.frame_scale, text="", wraplength=600)
        self.lbl_scale_status.grid(row=2, column=0, columnspan=3, sticky="w", padx=10)

        # --- KHU VUC 3: DANH SACH HIỂN THỊ ---
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Tình trạng Load Balancer & Danh sách Nodes")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # THÊM Ô TEXTBOX VÀO ĐÂY ĐỂ TRÁNH LỖI ATTRIBUTE ERROR
        self.txt_lb_info = ctk.CTkTextbox(self.list_frame, height=250)
        self.txt_lb_info.pack(fill="both", expand=True, padx=5, pady=5)

        self.active_pool_id = None
        self.active_subnet_id = None
        self.subnet_map = {}
        
        # Khởi chạy luồng lấy dữ liệu lúc mới mở Tab
        self.load_initial_subnets()
        self.load_data()

    # ================= CÁC HÀM XỬ LÝ LÕI =================

    def load_initial_subnets(self):
        def fetch():
            try:
                subnets = self.api.get_internal_subnets()
                if subnets:
                    self.subnet_map = {f"{s['name']} ({s['cidr']})": s['id'] for s in subnets}
                    self.combo_subnet.configure(values=list(self.subnet_map.keys()))
                    self.combo_subnet.set(list(self.subnet_map.keys())[0])
                else:
                    self.combo_subnet.configure(values=["Không có Subnet nội bộ"])
            except:
                pass
        threading.Thread(target=fetch).start()

    def update_textbox(self, text):
        try:
            self.txt_lb_info.configure(state="normal")
            self.txt_lb_info.delete("1.0", "end")
            self.txt_lb_info.insert("end", text)
            self.txt_lb_info.configure(state="disabled")
        except:
            pass

    def load_data(self):
        self.update_textbox("⏳ Đang kết nối OpenStack để tải dữ liệu, vui lòng đợi...\n")

        def fetch_data_bg():
            try:
                lbs = self.api.get_loadbalancers()
                if not lbs:
                    self.update_textbox("Chưa có Load Balancer nào được tạo.\n")
                    return
                
                lb = lbs[0]
                lb_ip = lb.get('vip_address', 'Không có IP')
                status = lb.get('provisioning_status', 'UNKNOWN')
                
                info_str = f"🚀 LB Name: {lb.get('name')} | IP Cổng: {lb_ip} | Status: {status}\n"
                info_str += "="*60 + "\n"
                
                res_pools = requests.get(f"{self.api.lb_base_url}/v2.0/lbaas/pools", headers=self.api.get_headers())
                pools = res_pools.json().get('pools', [])
                
                if pools:
                    pool_id = pools[0]['id']
                    self.active_pool_id = pool_id 
                    self.active_subnet_id = pools[0].get('vip_subnet_id')
                    
                    members = self.api.get_pool_members(pool_id)
                    if members:
                        info_str += f"🟢 Danh sách Web Nodes đang gánh tải ({len(members)} Node):\n\n"
                        for i, m in enumerate(members):
                            m_ip = m.get('address')
                            m_port = m.get('protocol_port')
                            m_status = m.get('provisioning_status', 'ACTIVE')
                            info_str += f"   {i+1}. IP: {m_ip}:{m_port}  --  Trạng thái: {m_status}\n"
                    else:
                        info_str += "⚠️ Cảnh báo: Load Balancer đang rỗng (Chưa có Member nào).\n"
                else:
                    info_str += "⚠️ Load Balancer chưa được cấu hình Pool.\n"
                    
                self.update_textbox(info_str)
                
            except Exception as e:
                self.update_textbox(f"[LỖI HIỂN THỊ] Không thể tải dữ liệu: {str(e)}")

        threading.Thread(target=fetch_data_bg).start()

    def init_lb_system(self):
        s_name = self.combo_subnet.get()
        if "Đang tải" in s_name or "Không có" in s_name: return
        s_id = self.subnet_map.get(s_name)
        self.active_subnet_id = s_id
        
        def run_task():
            try:
                self.lbl_lb_status.configure(text="[1/3] Đang tạo Load Balancer...", text_color="white")
                lb = self.api.create_loadbalancer("Nhom10_LB", s_id)
                lb_id = lb['id']

                max_retries = 20
                for i in range(max_retries):
                    self.lbl_lb_status.configure(text=f"[1/3] Chờ LB Active... (Lần {i+1}/{max_retries})", text_color="orange")
                    time.sleep(15) 
                    curr_lbs = self.api.get_loadbalancers()
                    target_lb = next((item for item in curr_lbs if item["id"] == lb_id), None)
                    if target_lb and target_lb.get('provisioning_status') == 'ACTIVE':
                        break
                    if i == max_retries - 1:
                        raise Exception("Hệ thống quá chậm, LB không kịp Active!")

                self.lbl_lb_status.configure(text="[2/3] Đang tạo Listener...", text_color="white")
                listener = self.api.create_listener(lb_id, "Nhom10_Listener")
                time.sleep(5) 

                self.lbl_lb_status.configure(text="[3/3] Đang tạo Pool...", text_color="white")
                pool = self.api.create_pool(listener['id'], "Nhom10_Pool")
                self.active_pool_id = pool['id']
                
                self.lbl_lb_status.configure(text="[SUCCESS] Hệ thống LB đã sẵn sàng!", text_color="#27ae60")
                self.load_data()
            except Exception as e:
                self.lbl_lb_status.configure(text=f"[ERROR] {str(e)}", text_color="#c0392b")
        
        threading.Thread(target=run_task).start()

    def scale_up(self):
        self.lbl_scale_status.configure(text="Đang khởi động tiến trình Scale Up...", text_color="white")

        def run_scale_logic():
            try:
                self.lbl_scale_status.configure(text="[0/3] Đang đồng bộ thông tin Load Balancer...", text_color="orange")
                
                # --- CHỐNG LỖI: LUÔN LẤY CHÍNH XÁC SUBNET TỪ LOAD BALANCER ---
                lbs = self.api.get_loadbalancers()
                if not lbs:
                    raise Exception("Không tìm thấy Load Balancer nào trên hệ thống!")
                self.active_subnet_id = lbs[0].get('vip_subnet_id')
                
                # Lấy Pool ID
                res_pools = requests.get(f"{self.api.lb_base_url}/v2.0/lbaas/pools", headers=self.api.get_headers())
                pools = res_pools.json().get('pools', [])
                if not pools:
                    raise Exception("Không tìm thấy Pool! Hãy tạo ở Bước 1.")
                self.active_pool_id = pools[0]['id']

                # BƯỚC 1: ĐÚC MÁY ẢO
                self.lbl_scale_status.configure(text="[1/3] Đang đúc máy ảo Web Server mới...", text_color="white")
                flavors = self.api.get_flavors()
                images = self.api.get_images()
                
                # Tìm Network ID dựa trên Subnet ID đã lấy chuẩn xác ở trên
                subnets = self.api.get_subnets()
                target_net_id = next((s['network_id'] for s in subnets if s['id'] == self.active_subnet_id), None)
                
                if not target_net_id: raise Exception("Không tìm thấy Network tương ứng với Pool!")

                udata = "#!/bin/bash\napt update -y\napt install -y nginx\necho '<h1>Node Scaled</h1>' > /var/www/html/index.html"
                vm_name = f"nhom10_scale_node_{int(time.time())}"
                
                res_vm = self.api.create_instance(vm_name, flavors[0]['id'], images[0]['id'], target_net_id, udata)
                vm_id = res_vm.get('server', {}).get('id')

                # BƯỚC 2: CHỜ IP NỘI BỘ
                ip_addr = None
                max_retries = 20 
                for i in range(max_retries):
                    self.lbl_scale_status.configure(text=f"[2/3] Đợi hệ thống cấp IP... ({i+1}/{max_retries})", text_color="orange")
                    time.sleep(5)
                    ports = self.api.get_instance_interfaces(vm_id)
                    if ports and len(ports) > 0:
                        f_ips = ports[0].get('fixed_ips', [])
                        if f_ips:
                            ip_addr = f_ips[0].get('ip_address')
                            break
                
                if not ip_addr: raise Exception("Không thể nhận IP nội bộ từ OpenStack.")

                # BƯỚC 3: CẮM VÀO LOAD BALANCER
                self.lbl_scale_status.configure(text=f"[3/3] Đang cắm IP {ip_addr} vào Load Balancer...", text_color="white")
                self.api.add_pool_member(self.active_pool_id, self.active_subnet_id, ip_addr)
                
                self.lbl_scale_status.configure(text=f"[SUCCESS] Đã thêm thành công VM {vm_name} vào hệ thống!", text_color="#27ae60")
                self.load_data()
                
            except Exception as e:
                self.lbl_scale_status.configure(text=f"[ERROR SCALING] {str(e)}", text_color="#c0392b")

        threading.Thread(target=run_scale_logic).start()

    def scale_down(self):
        self.lbl_scale_status.configure(text="Đang xử lý Scale Down...", text_color="white")

        def run_scale_down():
            try:
                if not hasattr(self, 'active_pool_id') or not self.active_pool_id:
                    res_pools = requests.get(f"{self.api.lb_base_url}/v2.0/lbaas/pools", headers=self.api.get_headers())
                    pools = res_pools.json().get('pools', [])
                    if pools: self.active_pool_id = pools[0]['id']
                    else:
                        self.lbl_scale_status.configure(text="[ERROR] Không tìm thấy Pool nào!", text_color="#c0392b")
                        return

                members = self.api.get_pool_members(self.active_pool_id)
                if not members:
                    self.lbl_scale_status.configure(text="Lỗi: Pool không còn máy ảo nào để xóa!", text_color="#c0392b")
                    return
                
                last_member = members[-1]
                member_ip = last_member['address']
                
                self.lbl_scale_status.configure(text=f"[1/2] Đang gỡ IP {member_ip} khỏi Load Balancer...", text_color="orange")
                self.api.remove_pool_member(self.active_pool_id, last_member['id'])
                
                self.lbl_scale_status.configure(text=f"[2/2] Đang xóa hoàn toàn máy ảo có IP {member_ip}...", text_color="orange")
                time.sleep(3) 
                
                servers = self.api.get_instances()
                target_server_id = None
                
                for s in servers:
                    addresses = s.get('addresses', {})
                    for net_info in addresses.values():
                        for ip_info in net_info:
                            if ip_info.get('addr') == member_ip:
                                target_server_id = s['id']
                                break
                
                if target_server_id:
                    self.api.delete_instance(target_server_id)
                    self.lbl_scale_status.configure(text=f"[SUCCESS] Đã gỡ khỏi LB và XÓA VM ({member_ip})!", text_color="#27ae60")
                else:
                    self.lbl_scale_status.configure(text=f"[SUCCESS] Đã gỡ IP {member_ip} khỏi LB (Không thấy VM để xóa).", text_color="#27ae60")
                    
                self.load_data()
            except Exception as e:
                self.lbl_scale_status.configure(text=f"[ERROR SCALING] {str(e)}", text_color="#c0392b")
                
        threading.Thread(target=run_scale_down).start()