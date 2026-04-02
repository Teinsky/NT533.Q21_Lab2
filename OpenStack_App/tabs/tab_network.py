import customtkinter as ctk

class NetworkDetailsWindow(ctk.CTkToplevel):
    def __init__(self, parent, api, network_data):
        super().__init__(parent)
        self.api = api
        self.net = network_data
        
        self.title(f"Network Details: {self.net.get('name', 'Unnamed')}")
        self.geometry("850x600")
        # Đảm bảo cửa sổ luôn nổi lên trên cùng
        self.attributes("-topmost", True)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_overview = self.tabs.add("Overview")
        self.tab_subnets = self.tabs.add("Subnets")
        self.tab_ports = self.tabs.add("Ports")

        self.setup_overview()
        self.setup_subnets()
        self.setup_ports()

    def setup_overview(self):
        info = (
            f"Tên Mạng: {self.net.get('name')}\n\n"
            f"ID: {self.net.get('id')}\n\n"
            f"Trạng thái (Status): {self.net.get('status')}\n\n"
            f"Admin State: {self.net.get('admin_state_up')}\n\n"
            f"Mạng chia sẻ (Shared): {self.net.get('shared')}\n\n"
            f"Mạng ngoài (External): {self.net.get('router:external')}"
        )
        ctk.CTkLabel(self.tab_overview, text=info, font=("Roboto", 14), justify="left").pack(anchor="w", padx=20, pady=20)

    def setup_subnets(self):
        # Form tạo Subnet mới cho mạng này
        form_frame = ctk.CTkFrame(self.tab_subnets)
        form_frame.pack(fill="x", pady=10, padx=10)
        
        self.entry_sub_name = ctk.CTkEntry(form_frame, placeholder_text="Tên Subnet mới", width=200)
        self.entry_sub_name.grid(row=0, column=0, padx=10, pady=10)
        
        self.entry_cidr = ctk.CTkEntry(form_frame, placeholder_text="CIDR (VD: 10.0.0.0/24)", width=200)
        self.entry_cidr.grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkButton(form_frame, text="Tạo Subnet", command=self.action_create_subnet).grid(row=0, column=2, padx=10, pady=10)
        
        self.lbl_sub_status = ctk.CTkLabel(form_frame, text="", text_color="red")
        self.lbl_sub_status.grid(row=1, column=0, columnspan=3, sticky="w", padx=10)

        # Danh sách Subnet
        self.list_subnets = ctk.CTkScrollableFrame(self.tab_subnets, label_text="Danh sách Subnets")
        self.list_subnets.pack(fill="both", expand=True, padx=10, pady=10)
        self.load_subnets()

    def load_subnets(self):
        for w in self.list_subnets.winfo_children(): w.destroy()
        subnets = self.api.get_subnets_by_network(self.net['id'])
        
        for sub in subnets:
            row = ctk.CTkFrame(self.list_subnets)
            row.pack(fill="x", pady=2)
            info = f"Tên: {sub.get('name')} | Địa chỉ: {sub.get('cidr')} | Gateway: {sub.get('gateway_ip')} | Phân loại: IPv{sub.get('ip_version')}"
            ctk.CTkLabel(row, text=info).pack(side="left", padx=10)
            ctk.CTkButton(row, text="Xóa", fg_color="#c0392b", width=60, 
                          command=lambda s_id=sub['id']: self.action_delete_subnet(s_id)).pack(side="right", padx=10)

    def action_create_subnet(self):
        name = self.entry_sub_name.get()
        cidr = self.entry_cidr.get()
        if name and cidr:
            try:
                self.api.create_subnet(self.net['id'], name, cidr)
                self.lbl_sub_status.configure(text="[SUCCESS] Đã tạo Subnet!", text_color="#27ae60")
                self.load_subnets()
            except Exception as e:
                self.lbl_sub_status.configure(text=f"[ERROR] {str(e)}", text_color="#c0392b")

    def action_delete_subnet(self, subnet_id):
        try:
            self.api.delete_subnet(subnet_id)
            self.lbl_sub_status.configure(text="[SUCCESS] Đã xóa Subnet!", text_color="#27ae60")
            self.load_subnets()
        except Exception as e:
            self.lbl_sub_status.configure(text=f"[ERROR] Không thể xóa: {str(e)}", text_color="#c0392b")

    def setup_ports(self):
        self.list_ports = ctk.CTkScrollableFrame(self.tab_ports, label_text="Các cổng (Ports) đang kết nối")
        self.list_ports.pack(fill="both", expand=True, padx=10, pady=10)
        self.load_ports()

    def load_ports(self):
        for w in self.list_ports.winfo_children(): w.destroy()
        ports = self.api.get_ports_by_network(self.net['id'])
        
        if not ports:
            ctk.CTkLabel(self.list_ports, text="Không có cổng nào đang kết nối.").pack(pady=10)
            
        for port in ports:
            row = ctk.CTkFrame(self.list_ports)
            row.pack(fill="x", pady=2)
            
            ips = ", ".join([ip.get('ip_address') for ip in port.get('fixed_ips', [])])
            info = f"Tên: {port.get('name') or 'N/A'} | MAC: {port.get('mac_address')} | IP: {ips} | Status: {port.get('status')}"
            ctk.CTkLabel(row, text=info).pack(side="left", padx=10)

# --- CLASS GIAO DIỆN CHÍNH CỦA TAB NETWORK ---
class NetworkTab(ctk.CTkFrame):
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api

        ctk.CTkLabel(self, text="2. Quản lý Mạng (Networks)", font=("Roboto", 20, "bold")).pack(pady=10, anchor="w", padx=10)

        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(fill="x", pady=10, padx=10)
        
        # Form tạo mạng gốc
        self.entry_net_name = ctk.CTkEntry(self.form_frame, placeholder_text="Tên Network", width=200)
        self.entry_net_name.grid(row=0, column=0, padx=10, pady=10)
        
        self.entry_sub_name = ctk.CTkEntry(self.form_frame, placeholder_text="Tên Subnet đầu tiên", width=200)
        self.entry_sub_name.grid(row=0, column=1, padx=10, pady=10)
        
        self.entry_cidr = ctk.CTkEntry(self.form_frame, placeholder_text="CIDR (VD: 192.168.10.0/24)", width=200)
        self.entry_cidr.grid(row=0, column=2, padx=10, pady=10)
        
        ctk.CTkButton(self.form_frame, text="Tạo Network & Subnet", command=self.create_net).grid(row=0, column=3, padx=10, pady=10)

        self.lbl_status = ctk.CTkLabel(self.form_frame, text="", font=("Roboto", 14), wraplength=750, justify="left")
        self.lbl_status.grid(row=1, column=0, columnspan=4, pady=5, sticky="w", padx=10)

        # Bảng liệt kê
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Danh sách Networks hiện có")
        self.list_frame.pack(fill="both", expand=True, pady=10, padx=10)
        self.load_networks()

    def load_networks(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        networks = self.api.get_networks()
        for net in networks:
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", pady=2)
            
            info = f"Tên: {net.get('name')} | Trạng thái: {net.get('status')} | Phân loại: {'External' if net.get('router:external') else 'Internal'}"
            ctk.CTkLabel(row, text=info).pack(side="left", padx=10)
            
            # Khối nút bấm bên phải
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="right")

            # Nút xem chi tiết
            ctk.CTkButton(btn_frame, text="Chi tiết", fg_color="#2980b9", width=60, 
                          command=lambda n=net: self.open_details(n)).pack(side="left", padx=5)

            # Không cho xóa mạng ngoài
            if not net.get('router:external'):
                ctk.CTkButton(btn_frame, text="Xóa", fg_color="#c0392b", width=60, 
                              command=lambda n_id=net['id']: self.delete_net(n_id)).pack(side="left", padx=5)

    def open_details(self, network_data):
        # Mở cửa sổ popup chi tiết
        NetworkDetailsWindow(self, self.api, network_data)

    def create_net(self):
        net_name = self.entry_net_name.get()
        sub_name = self.entry_sub_name.get()
        cidr = self.entry_cidr.get()
        
        if not net_name:
            self.lbl_status.configure(text="[WARNING] Vui lòng nhập Tên Mạng.", text_color="orange")
            return

        try:
            res = self.api.create_network(net_name)
            net_id = res.get('network', {}).get('id')
            if net_id and sub_name and cidr:
                self.api.create_subnet(net_id, sub_name, cidr)
            
            self.lbl_status.configure(text=f"[SUCCESS] Đã tạo thành công Network '{net_name}'", text_color="#27ae60")
            self.load_networks()
        except Exception as e:
            self.lbl_status.configure(text=f"[ERROR] Quá trình tạo thất bại: {str(e)}", text_color="#c0392b")

    def delete_net(self, net_id):
        try:
            self.api.delete_network(net_id)
            self.lbl_status.configure(text="[SUCCESS] Đã xóa Network thành công!", text_color="#27ae60")
            self.load_networks()
        except Exception as e:
            self.lbl_status.configure(text=f"[ERROR] Không thể xóa: {str(e)}", text_color="#c0392b")
