import customtkinter as ctk

class ConstraintsTab(ctk.CTkFrame):
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api

        ctk.CTkLabel(self, text="0. Limit Summary", font=("Roboto", 20, "bold")).pack(pady=10, anchor="w", padx=10)

        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(fill="x", padx=10, pady=10)
        
        self.lbl_info = ctk.CTkLabel(self.info_frame, text="Đang tải dữ liệu...", font=("Consolas", 15), justify="left")
        self.lbl_info.pack(pady=20, padx=20)

        ctk.CTkButton(self, text="Cập nhật Limits", command=self.load_data).pack(pady=10)
        self.load_data()

    def load_data(self):
        limits = self.api.get_limits()
        if limits:
            text = (
                f"TÀI NGUYÊN COMPUTE (NOVA)\n"
                f"---------------------------------\n"
                f"Instances Used: {limits.get('totalInstancesUsed', 0)} of {limits.get('maxTotalInstances', 'No Limit')}\n"
                f"VCPUs Used:     {limits.get('totalCoresUsed', 0)} of {limits.get('maxTotalCores', 'No Limit')}\n"
                f"RAM Used:       {limits.get('totalRAMUsed', 0)} MB of {limits.get('maxTotalRAMSize', 'No Limit')} MB\n"
            )
            self.lbl_info.configure(text=text)
        else:
            self.lbl_info.configure(text="Không thể lấy thông tin giới hạn (Quota).")
