import customtkinter as ctk
from api_manager import OpenStackAPI
from tabs.tab_flavor_image import FlavorImageTab
from tabs.tab_network import NetworkTab
from tabs.tab_router import RouterTab
from tabs.tab_instance import InstanceTab
from tabs.tab_floating_ip import FloatingIPTab
from tabs.tab_constraints import ConstraintsTab
from tabs.tab_lb_scaling import LBScalingTab

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OpenStack Horizon Clone")
        self.geometry("1100x700")
        self.api = OpenStackAPI()

        # Grid layout: 1 cot sidebar, 1 cot noi dung
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="NC-Cloud Panel", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Khung dang nhap
        self.entry_user = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Username")
        self.entry_user.grid(row=1, column=0, padx=20, pady=5)
        self.entry_pass = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Password", show="*")
        self.entry_pass.grid(row=2, column=0, padx=20, pady=5)
        self.entry_proj = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Project")
        self.entry_proj.insert(0, "NT533.Q21.G10")
        self.entry_proj.grid(row=3, column=0, padx=20, pady=5)
        
        self.btn_login = ctk.CTkButton(self.sidebar_frame, text="Login", command=self.login_event)
        self.btn_login.grid(row=4, column=0, padx=20, pady=10)

        # Main Content Frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.current_tab = None

    def login_event(self):
        u, p, proj = self.entry_user.get(), self.entry_pass.get(), self.entry_proj.get()
        
        # 1. Đổi trạng thái nút bấm để biết app đang chạy
        self.btn_login.configure(text="Đang xác thực...", state="disabled")
        self.update() # Ép giao diện render lại trạng thái nút bấm ngay lập tức

        try:
            # 2. Gửi request
            if self.api.login(u, p, proj):
                self.btn_login.configure(text="Đăng nhập thành công!", fg_color="green")
                self.setup_navigation()
                self.show_tab("Network") 
            else:
                # Nếu sai tài khoản / mật khẩu / project
                self.btn_login.configure(text="Sai thông tin!", state="normal", fg_color="#c0392b")
        except Exception as e:
            # Nếu mất mạng hoặc hệ thống OpenStack đang sập
            print(f"Lỗi kết nối: {e}")
            self.btn_login.configure(text="Lỗi mạng!", state="normal", fg_color="#c0392b")

    def setup_navigation(self):
        # Tạo một vùng chứa (Frame) riêng cho menu để dồn chúng lên trên
        nav_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        nav_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkButton(nav_frame, text="0. Constraints (Limits)", command=lambda: self.show_tab("Constraints")).pack(pady=5, fill="x")
        ctk.CTkButton(nav_frame, text="1. Flavors & Images", command=lambda: self.show_tab("FlavorImage")).pack(pady=5, fill="x")
        ctk.CTkButton(nav_frame, text="2. Networks", command=lambda: self.show_tab("Network")).pack(pady=5, fill="x")
        ctk.CTkButton(nav_frame, text="3. Routers", command=lambda: self.show_tab("Router")).pack(pady=5, fill="x")
        ctk.CTkButton(nav_frame, text="4. Instances", command=lambda: self.show_tab("Instance")).pack(pady=5, fill="x")
        ctk.CTkButton(nav_frame, text="5. Floating IPs", command=lambda: self.show_tab("FloatingIP")).pack(pady=5, fill="x")
        
        # ĐÂY LÀ CHỖ CHÈN NÚT BẤM CHO TÂM
        ctk.CTkButton(nav_frame, text="6. Cân Bằng Tải & Scale", command=lambda: self.show_tab("LBScaling"), fg_color="#8e44ad", hover_color="#9b59b6").pack(pady=5, fill="x")

    def show_tab(self, tab_name):
        if self.current_tab is not None:
            self.current_tab.destroy()

        if tab_name == "Constraints": self.current_tab = ConstraintsTab(self.main_frame, self.api)
        elif tab_name == "FlavorImage": self.current_tab = FlavorImageTab(self.main_frame, self.api)
        elif tab_name == "Network": self.current_tab = NetworkTab(self.main_frame, self.api)
        elif tab_name == "Router": self.current_tab = RouterTab(self.main_frame, self.api)
        elif tab_name == "Instance": self.current_tab = InstanceTab(self.main_frame, self.api)
        elif tab_name == "FloatingIP": self.current_tab = FloatingIPTab(self.main_frame, self.api)
        
        # ĐÂY LÀ CHỖ KHAI BÁO CLASS TAB CHO TÂM
        elif tab_name == "LBScaling": self.current_tab = LBScalingTab(self.main_frame, self.api)
            
        self.current_tab.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()