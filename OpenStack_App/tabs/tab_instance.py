import customtkinter as ctk

class InstanceDetailsWindow(ctk.CTkToplevel):
    def __init__(self, parent, api, instance_data):
        super().__init__(parent)
        self.api = api
        self.instance = instance_data
        
        self.title(f"Instance Details: {self.instance.get('name')}")
        self.geometry("900x650")
        self.attributes("-topmost", True)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_overview = self.tabs.add("Overview")
        self.tab_interfaces = self.tabs.add("Interfaces")
        self.tab_log = self.tabs.add("Log")
        self.tab_console = self.tabs.add("Console")
        self.tab_actions = self.tabs.add("Action Log")

        self.setup_overview()
        self.setup_interfaces()
        self.setup_log()
        self.setup_console()
        self.setup_actions()

    def setup_overview(self):
        addresses = self.instance.get('addresses', {})
        ip_info = ""
        for net_name, ip_list in addresses.items():
            ips = ", ".join([ip['addr'] for ip in ip_list])
            ip_info += f"  - {net_name}: {ips}\n"

        info = (
            f"Ten May Ao: {self.instance.get('name')}\n\n"
            f"ID: {self.instance.get('id')}\n\n"
            f"Trang thai (Status): {self.instance.get('status')}\n\n"
            f"Availability Zone: {self.instance.get('OS-EXT-AZ:availability_zone')}\n\n"
            f"Power State: {self.instance.get('OS-EXT-STS:power_state')}\n\n"
            f"Dia chi IP:\n{ip_info}"
        )
        ctk.CTkLabel(self.tab_overview, text=info, font=("Roboto", 14), justify="left").pack(anchor="w", padx=20, pady=20)

    def setup_interfaces(self):
        list_interfaces = ctk.CTkScrollableFrame(self.tab_interfaces)
        list_interfaces.pack(fill="both", expand=True, padx=10, pady=10)
        
        ports = self.api.get_instance_interfaces(self.instance['id'])
        if not ports:
            ctk.CTkLabel(list_interfaces, text="Khong tim thay interface nao.").pack(pady=10)
            
        for port in ports:
            row = ctk.CTkFrame(list_interfaces)
            row.pack(fill="x", pady=2)
            
            ips = ", ".join([ip.get('ip_address') for ip in port.get('fixed_ips', [])])
            info = f"MAC: {port.get('mac_address')} | IP: {ips} | Trang thai: {port.get('status')} | Mang ID: {port.get('network_id')[:10]}..."
            ctk.CTkLabel(row, text=info).pack(side="left", padx=10, pady=10)

    def setup_log(self):
        top_frame = ctk.CTkFrame(self.tab_log, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(top_frame, text="Log Length (So dong):").pack(side="left", padx=5)
        self.entry_log_length = ctk.CTkEntry(top_frame, width=80)
        self.entry_log_length.insert(0, "35")
        self.entry_log_length.pack(side="left", padx=5)
        
        ctk.CTkButton(top_frame, text="View Log", command=self.load_log, width=100).pack(side="left", padx=10)
        
        self.textbox_log = ctk.CTkTextbox(self.tab_log, font=("Consolas", 12))
        self.textbox_log.pack(fill="both", expand=True, padx=10, pady=10)
        self.load_log()

    def load_log(self):
        length = self.entry_log_length.get()
        length = int(length) if length.isdigit() else 35
        
        log_data = self.api.get_instance_log(self.instance['id'], length)
        self.textbox_log.delete("0.0", "end")
        self.textbox_log.insert("0.0", log_data)

    def setup_console(self):
        ctk.CTkLabel(self.tab_console, text="VNC Console URL", font=("Roboto", 16, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self.tab_console, text="Copy duong dan duoi day va dan vao trinh duyet de dieu khien may ao:").pack(pady=5)
        
        self.textbox_console = ctk.CTkTextbox(self.tab_console, height=60)
        self.textbox_console.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(self.tab_console, text="Lay URL Console", command=self.load_console).pack(pady=10)

    def load_console(self):
        url = self.api.get_instance_console(self.instance['id'])
        self.textbox_console.delete("0.0", "end")
        self.textbox_console.insert("0.0", url)

    def setup_actions(self):
        list_actions = ctk.CTkScrollableFrame(self.tab_actions)
        list_actions.pack(fill="both", expand=True, padx=10, pady=10)
        
        actions = self.api.get_instance_actions(self.instance['id'])
        if not actions:
            ctk.CTkLabel(list_actions, text="Khong co lich su hanh dong.").pack(pady=10)
            
        for act in actions:
            row = ctk.CTkFrame(list_actions)
            row.pack(fill="x", pady=2)
            
            info = f"Hanh dong: {act.get('action')} | Thoi gian: {act.get('start_time')} | Request ID: {act.get('request_id')}"
            ctk.CTkLabel(row, text=info).pack(side="left", padx=10, pady=10)


# --- CLASS GIAO DIEN CHINH CUA TAB INSTANCE ---
class InstanceTab(ctk.CTkFrame):
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api
        
        self.flavor_map = {}
        self.image_map = {}
        self.network_map = {}

        ctk.CTkLabel(self, text="4. Khoi tao May ao (Launch Instance)", font=("Roboto", 20, "bold")).pack(pady=10, anchor="w", padx=10)

        self.form = ctk.CTkFrame(self)
        self.form.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(self.form, text="Ten may ao:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(self.form, text="Cau hinh (Flavor):").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(self.form, text="He dieu hanh (Image):").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(self.form, text="Mang noi bo:").grid(row=3, column=0, padx=10, pady=10, sticky="w")

        self.entry_name = ctk.CTkEntry(self.form, width=250)
        self.entry_name.grid(row=0, column=1, padx=10, pady=10)

        self.combo_flavor = ctk.CTkComboBox(self.form, width=250)
        self.combo_flavor.grid(row=1, column=1, padx=10, pady=10)
        
        self.combo_image = ctk.CTkComboBox(self.form, width=250)
        self.combo_image.grid(row=2, column=1, padx=10, pady=10)

        self.combo_net = ctk.CTkComboBox(self.form, width=250)
        self.combo_net.grid(row=3, column=1, padx=10, pady=10)

        ctk.CTkLabel(self.form, text="User Data Script:").grid(row=0, column=2, sticky="sw", padx=10)
        self.text_userdata = ctk.CTkTextbox(self.form, width=350, height=150)
        self.text_userdata.grid(row=1, column=2, rowspan=3, padx=10, pady=10)
        
        script = "#!/bin/bash\napt update -y\napt install -y nginx\necho 'Web Service - UIT' > /var/www/html/index.html"
        self.text_userdata.insert("0.0", script)

        ctk.CTkButton(self.form, text="Launch Instance", command=self.launch_vm).grid(row=4, column=0, columnspan=3, pady=10)

        self.lbl_status = ctk.CTkLabel(self.form, text="")
        self.lbl_status.grid(row=5, column=0, columnspan=3, pady=5)

        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Danh sach may ao dang chay")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_dropdowns()
        self.load_instances()

    def load_dropdowns(self):
        flavors = self.api.get_flavors()
        self.flavor_map = {f['name']: f['id'] for f in flavors}
        self.combo_flavor.configure(values=list(self.flavor_map.keys()) if flavors else ["Trong"])
        if flavors: self.combo_flavor.set(list(self.flavor_map.keys())[0])

        images = self.api.get_images()
        self.image_map = {i['name']: i['id'] for i in images}
        self.combo_image.configure(values=list(self.image_map.keys()) if images else ["Trong"])
        if images: self.combo_image.set(list(self.image_map.keys())[0])

        networks = self.api.get_networks()
        self.network_map = {n['name']: n['id'] for n in networks if not n.get('router:external')}
        self.combo_net.configure(values=list(self.network_map.keys()) if self.network_map else ["Trong"])
        if self.network_map: self.combo_net.set(list(self.network_map.keys())[0])

    def load_instances(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        servers = self.api.get_instances()
        for srv in servers:
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=f"Ten: {srv['name']} | Trang thai: {srv['status']}").pack(side="left", padx=10)
            
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="right")
            
            ctk.CTkButton(btn_frame, text="Xoa", fg_color="#c0392b", width=60, 
                          command=lambda s_id=srv['id']: self.delete_vm(s_id)).pack(side="right", padx=5)
            ctk.CTkButton(btn_frame, text="Chi tiet", fg_color="#2980b9", width=60, 
                          command=lambda s_data=srv: self.open_details(s_data)).pack(side="right", padx=5)

    def open_details(self, instance_data):
        InstanceDetailsWindow(self, self.api, instance_data)

    def launch_vm(self):
        name = self.entry_name.get()
        f_id = self.flavor_map.get(self.combo_flavor.get())
        img_id = self.image_map.get(self.combo_image.get())
        net_id = self.network_map.get(self.combo_net.get())
        udata = self.text_userdata.get("0.0", "end").strip()
        
        if name and f_id and img_id and net_id:
            try:
                self.lbl_status.configure(text="Dang gui request tao may ao...", text_color="white")
                self.update()
                self.api.create_instance(name, f_id, img_id, net_id, udata)
                self.lbl_status.configure(text="[SUCCESS] Da gui lenh tao may ao. Vui long doi he thong khoi dong.", text_color="green")
                self.load_instances()
            except Exception as e:
                self.lbl_status.configure(text=f"[ERROR] {str(e)}", text_color="red")

    def delete_vm(self, vm_id):
        try:
            self.api.delete_instance(vm_id)
            self.load_instances()
        except Exception as e:
            self.lbl_status.configure(text=f"[ERROR] {str(e)}", text_color="red")
