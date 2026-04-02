import customtkinter as ctk

class RouterDetailsWindow(ctk.CTkToplevel):
    def __init__(self, parent, api, router_data, refresh_callback):
        super().__init__(parent)
        self.api = api
        self.router = router_data
        self.refresh_callback = refresh_callback
        
        self.title(f"Router Details: {self.router.get('name')}")
        self.geometry("800x550")
        self.attributes("-topmost", True)

        self.subnet_map = {}

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_overview = self.tabs.add("Overview")
        self.tab_interfaces = self.tabs.add("Interfaces")

        self.setup_overview()
        self.setup_interfaces()

    def setup_overview(self):
        ext_gw = self.router.get('external_gateway_info')
        ext_net = ext_gw.get('network_id') if ext_gw else "None"
        
        info = (
            f"Tên Router: {self.router.get('name')}\n\n"
            f"ID: {self.router.get('id')}\n\n"
            f"Trang thai: {self.router.get('status')}\n\n"
            f"External Gateway Network: {ext_net}\n\n"
            f"Admin State: {'UP' if self.router.get('admin_state_up') else 'DOWN'}"
        )
        ctk.CTkLabel(self.tab_overview, text=info, font=("Roboto", 14), justify="left").pack(anchor="w", padx=20, pady=20)

    def setup_interfaces(self):
        # Khu vuc them Interface
        form_frame = ctk.CTkFrame(self.tab_interfaces)
        form_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(form_frame, text="Chọn Subnet để kết nối:").grid(row=0, column=0, padx=10, pady=10)
        self.combo_sub = ctk.CTkComboBox(form_frame, width=250)
        self.combo_sub.grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkButton(form_frame, text="Add Interface", command=self.add_interface).grid(row=0, column=2, padx=10, pady=10)
        
        self.lbl_status = ctk.CTkLabel(form_frame, text="", wraplength=500)
        self.lbl_status.grid(row=1, column=0, columnspan=3, pady=5)

        # Bang liet ke Interface hien co
        self.list_frame = ctk.CTkScrollableFrame(self.tab_interfaces, label_text="Interfaces (Subnets) đã kết nối")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_interfaces()

    def load_interfaces(self):
        # Load Subnet vao Dropdown
        all_subs = self.api.get_internal_subnets()
        self.subnet_map = {f"{s['name']} ({s['cidr']})": s['id'] for s in all_subs}
        self.combo_sub.configure(values=list(self.subnet_map.keys()) if self.subnet_map else ["Trong"])
        
        # Load danh sach tren Router
        for w in self.list_frame.winfo_children(): w.destroy()
        interfaces = self.api.get_router_interfaces(self.router['id'])
        
        for port in interfaces:
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", pady=2)
            
            fixed_ips = port.get('fixed_ips', [])
            ip_addr = fixed_ips[0].get('ip_address') if fixed_ips else "N/A"
            sub_id = fixed_ips[0].get('subnet_id') if fixed_ips else None
            
            ctk.CTkLabel(row, text=f"IP: {ip_addr} | Port ID: {port['id'][:10]}...").pack(side="left", padx=10)
            
            if sub_id:
                ctk.CTkButton(row, text="Delete", fg_color="#c0392b", width=60,
                              command=lambda s=sub_id: self.delete_interface(s)).pack(side="right", padx=10)

    def add_interface(self):
        s_id = self.subnet_map.get(self.combo_sub.get())
        if s_id:
            try:
                self.api.add_router_interface(self.router['id'], s_id)
                self.lbl_status.configure(text="[SUCCESS] Đã nối subnet!", text_color="green")
                self.load_interfaces()
                self.refresh_callback() # Cap nhat lai man hinh chinh
            except Exception as e:
                self.lbl_status.configure(text=f"[ERROR] {str(e)}", text_color="red")

    def delete_interface(self, subnet_id):
        try:
            self.api.remove_router_interface(self.router['id'], subnet_id)
            self.load_interfaces()
            self.refresh_callback()
        except Exception as e:
            self.lbl_status.configure(text=f"[ERROR] {str(e)}", text_color="red")

class RouterTab(ctk.CTkFrame):
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api

        ctk.CTkLabel(self, text="3. Quản lý Router", font=("Roboto", 20, "bold")).pack(pady=10, anchor="w", padx=10)

        # Form tao Router
        self.form = ctk.CTkFrame(self)
        self.form.pack(fill="x", padx=10, pady=10)
        
        self.entry_name = ctk.CTkEntry(self.form, placeholder_text="Tên Router", width=250)
        self.entry_name.grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkButton(self.form, text="Create Router & Gateway", command=self.create_router).grid(row=0, column=1, padx=10)

        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Danh sách Router")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_data()

    def load_data(self):
        for w in self.list_frame.winfo_children(): w.destroy()
        
        # Lay ten subnet de hien thi nhanh o ngoai
        all_subs = {s['id']: s['name'] for s in self.api.get_internal_subnets()}
        
        for r in self.api.get_routers():
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", pady=2)
            
            gw = "Connected" if r.get('external_gateway_info') else "Disconnected"
            sub_ids = self.api.get_router_attached_subnets(r['id'])
            sub_names = [all_subs.get(sid, sid[:8]) for sid in sub_ids]
            
            info = f"Router: {r['name']} | Gateway: {gw} | Interfaces: [{', '.join(sub_names)}]"
            ctk.CTkLabel(row, text=info).pack(side="left", padx=10)
            
            ctk.CTkButton(row, text="Xóa", fg_color="#c0392b", width=60, 
                          command=lambda rid=r['id']: self.delete_router(rid)).pack(side="right", padx=5)
            ctk.CTkButton(row, text="Chi tiết", fg_color="#2980b9", width=60, 
                          command=lambda rd=r: self.open_details(rd)).pack(side="right", padx=5)

    def open_details(self, router_data):
        RouterDetailsWindow(self, self.api, router_data, self.load_data)

    def create_router(self):
        name = self.entry_name.get()
        if name:
            res = self.api.create_router(name)
            rid = res.get('router', {}).get('id')
            ext_net = self.api.get_external_network()
            if rid and ext_net:
                self.api.set_router_gateway(rid, ext_net)
            self.load_data()

    def delete_router(self, rid):
        try:
            self.api.delete_router(rid)
            self.load_data()
        except Exception as e:
            print(f"Loi: {e}")
