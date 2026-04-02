import customtkinter as ctk

class FloatingIPTab(ctk.CTkFrame):
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api

        # Dictionary de map ten thanh ID cho combobox
        self.dict_instances = {}
        self.dict_fips = {}

        ctk.CTkLabel(self, text="5. Quản lý Floating IP (Public IP)", font=("Roboto", 20, "bold")).pack(pady=10, anchor="w", padx=10)

        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(fill="x", padx=10, pady=10)

        # Hanh dong 1: Cap phat IP moi tu OpenStack
        ctk.CTkLabel(self.form_frame, text="Xin cấp phát IP Public mới:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkButton(self.form_frame, text="Allocate Floating IP", command=self.allocate_ip).grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Hanh dong 2: Gan IP vao May ao dang chay
        ctk.CTkLabel(self.form_frame, text="Gắn IP vào Máy ảo:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.combo_fip = ctk.CTkComboBox(self.form_frame, width=200, values=["Loading..."])
        self.combo_fip.grid(row=1, column=1, padx=10, pady=10)

        self.combo_instance = ctk.CTkComboBox(self.form_frame, width=200, values=["Loading..."])
        self.combo_instance.grid(row=1, column=2, padx=10, pady=10)

        ctk.CTkButton(self.form_frame, text="Associate IP", fg_color="green", command=self.associate_ip).grid(row=1, column=3, padx=10, pady=10)

        # Bang danh sach IP hien co
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Danh sách Floating IP hiện có")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_data()

    def load_data(self):
        # Xoa du lieu cu tren bang
        for w in self.list_frame.winfo_children(): 
            w.destroy()
        
        # Goi API lay du lieu
        fips = self.api.get_floating_ips()
        instances = self.api.get_instances()
        
        # Map ten may ao voi ID
        self.dict_instances = {srv['name']: srv['id'] for srv in instances}
        
        # Chi lay nhung IP chua duoc gan (port_id la None) de dua vao dropdown
        self.dict_fips = {fip['floating_ip_address']: fip['id'] for fip in fips if not fip.get('port_id')}
        
        # Cap nhat Dropdown Floating IP
        if self.dict_fips:
            self.combo_fip.configure(values=list(self.dict_fips.keys()))
            self.combo_fip.set(list(self.dict_fips.keys())[0])
        else:
            self.combo_fip.configure(values=["[Không có IP rảnh]"])
            self.combo_fip.set("[Không có IP rảnh]")

        # Cap nhat Dropdown Instances
        if self.dict_instances:
            self.combo_instance.configure(values=list(self.dict_instances.keys()))
            self.combo_instance.set(list(self.dict_instances.keys())[0])
        else:
            self.combo_instance.configure(values=["[Không có máy ảo]"])
            self.combo_instance.set("[Không có máy ảo]")

        # Do du lieu ra bang (ScrollableFrame)
        for fip in fips:
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", pady=2)
            
            # Kiem tra xem IP nay da bi gan vao may nao chua
            status = f"[Đã gắn - Port: {fip.get('port_id')[:8]}...]" if fip.get('port_id') else "[Đang rảnh]"
            info = f"IP: {fip['floating_ip_address']}  |  Trạng thái: {status}  |  ID: {fip['id'][:8]}..."
            
            ctk.CTkLabel(row, text=info).pack(side="left", padx=10)

    def allocate_ip(self):
        self.api.allocate_floating_ip()
        self.load_data() # Refresh UI sau khi tao

    def associate_ip(self):
        ip_addr = self.combo_fip.get()
        vm_name = self.combo_instance.get()
        
        fip_id = self.dict_fips.get(ip_addr)
        vm_id = self.dict_instances.get(vm_name)
        
        if fip_id and vm_id:
            self.api.associate_floating_ip(vm_id, fip_id)
            self.load_data() # Refresh UI sau khi gan
