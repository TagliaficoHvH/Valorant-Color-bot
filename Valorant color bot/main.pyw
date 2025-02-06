import pyautogui
import keyboard
import time
import cv2
import numpy as np
from mss import mss
import tkinter as tk
from tkinter import ttk
from threading import Thread
import json
import os

CONFIG_FILE = "config.json"

class ColorDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TagliaficoHvH123")
        self.root.geometry("500x600")
        self.root.configure(bg="#1d1d1d")  # Fondo principal en color oscuro

        # Cambiar el ícono de la ventana
        try:
            self.root.iconbitmap("TGFC.ico")  # Asegúrate de tener un archivo "icon.ico" en el mismo directorio
        except Exception as e:
            print("No se pudo cargar el ícono. Asegúrate de que 'icon.ico' exista.")

        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Configuración de estilos
        self.style.configure(
            "TScale", background="#1d1d1d", troughcolor="#ff8c00", sliderthickness=20, sliderrelief="flat"
        )
        self.style.configure(
            "TButton", font=("Arial", 12), padding=10, background="#ff8c00", foreground="#FFFFFF"
        )
        self.style.map(
            "TButton",
            background=[("active", "#ff8c00"), ("pressed", "#ff4500")],
            relief=[("pressed", "sunken"), ("!pressed", "flat")]
        )
        self.style.configure(
            "TRadiobutton", background="#1d1d1d", foreground="#ff8c00", font=("Arial", 12)
        )

        # Cargar configuración desde el archivo o usar valores predeterminados
        self.config = self.load_config()
        self.running = False
        self.fov_radius = self.config.get("fov_radius", 6)
        self.selected_color = tk.StringVar(value=self.config.get("selected_color", "yellow"))
        self.trigger_key = tk.StringVar(value=self.config.get("trigger_key", "k"))
        self.activation_key = tk.StringVar(value=self.config.get("activation_key", "alt"))
        self.shot_cooldown = tk.DoubleVar(value=self.config.get("shot_cooldown", 0.5))
        self.fps = tk.IntVar(value=self.config.get("fps", 120))  # Valor predeterminado: 120 FPS
        self.screen_width, self.screen_height = pyautogui.size()
        self.center_x, self.center_y = self.screen_width // 2, self.screen_height // 2
        self.last_shot_time = 0

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg="#1d1d1d")
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Título sin animación
        title_label = tk.Label(
            main_frame, text="Color Bot", font=("Arial", 18, "bold"), bg="#1d1d1d", fg="#ff8c00"
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Opciones del usuario
        tk.Label(
            main_frame, text="Color to Detect:", font=("Arial", 12), bg="#1d1d1d", fg="#ff8c00"
        ).grid(row=1, column=0, padx=10, pady=5, sticky="e")

        colors = ["Yellow", "Red", "Purple"]
        self.color_combobox = ttk.Combobox(
            main_frame, values=colors, textvariable=self.selected_color, state="readonly", width=10
        )
        self.color_combobox.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.color_combobox.set(self.selected_color.get())

        tk.Label(
            main_frame, text="FOV Size:", font=("Arial", 12), bg="#1d1d1d", fg="#ff8c00"
        ).grid(row=2, column=0, padx=10, pady=5, sticky="e")

        self.fov_slider = ttk.Scale(
            main_frame, from_=1, to=100, orient="horizontal", command=self.update_fov, style="TScale"
        )
        self.fov_slider.set(self.fov_radius)
        self.fov_slider.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        self.fov_value_label = tk.Label(
            main_frame, text=f"{self.fov_radius}", font=("Arial", 12), bg="#1d1d1d", fg="#ff8c00"
        )
        self.fov_value_label.grid(row=2, column=2, padx=10, pady=5, sticky="w")

        tk.Label(
            main_frame, text="Trigger Key:", font=("Arial", 12), bg="#1d1d1d", fg="#ff8c00"
        ).grid(row=3, column=0, padx=10, pady=5, sticky="e")

        self.trigger_key_entry = ttk.Entry(main_frame, textvariable=self.trigger_key, width=10)
        self.trigger_key_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        tk.Label(
            main_frame, text="Activation Key (hold):", font=("Arial", 12), bg="#1d1d1d", fg="#ff8c00"
        ).grid(row=4, column=0, padx=10, pady=5, sticky="e")

        self.activation_key_entry = ttk.Entry(main_frame, textvariable=self.activation_key, width=10)
        self.activation_key_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        tk.Label(
            main_frame, text="Shot Cooldown (s):", font=("Arial", 12), bg="#1d1d1d", fg="#ff8c00"
        ).grid(row=5, column=0, padx=10, pady=5, sticky="e")

        self.cooldown_slider = ttk.Scale(
            main_frame, from_=0, to=1, orient="horizontal", variable=self.shot_cooldown,
            command=self.update_cooldown, style="TScale"
        )
        self.cooldown_slider.set(self.shot_cooldown.get())
        self.cooldown_slider.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        self.cooldown_value_label = tk.Label(
            main_frame, text=f"{self.shot_cooldown.get():.2f}", font=("Arial", 12), bg="#1d1d1d", fg="#ff8c00"
        )
        self.cooldown_value_label.grid(row=5, column=2, padx=10, pady=5, sticky="w")

        tk.Label(
            main_frame, text="FPS:", font=("Arial", 12), bg="#1d1d1d", fg="#ff8c00"
        ).grid(row=6, column=0, padx=10, pady=5, sticky="e")

        self.fps_slider = ttk.Scale(
            main_frame, from_=60, to=240, orient="horizontal", variable=self.fps,
            command=self.update_fps, style="TScale"
        )
        self.fps_slider.set(self.fps.get())  # Valor predeterminado: 120 FPS
        self.fps_slider.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

        self.fps_value_label = tk.Label(
            main_frame, text=f"{self.fps.get()}", font=("Arial", 12), bg="#1d1d1d", fg="#ff8c00"
        )
        self.fps_value_label.grid(row=6, column=2, padx=10, pady=5, sticky="w")

        self.start_button = ttk.Button(
            main_frame, text="Start Detection", command=self.toggle_detection, style="TButton"
        )
        self.start_button.grid(row=7, column=0, columnspan=3, pady=20)

        self.status_label = tk.Label(
            main_frame, text="Status: Stopped", font=("Arial", 12), bg="#1d1d1d", fg="#FF4500"
        )
        self.status_label.grid(row=8, column=0, columnspan=3, pady=5)

        tk.Label(
            main_frame, text="Press 'Insert' to exit.", font=("Arial", 10), bg="#1d1d1d", fg="#ff8c00"
        ).grid(row=9, column=0, columnspan=3, pady=5)

    def update_fov(self, value):
        self.fov_radius = int(float(value))
        self.fov_value_label.config(text=f"{self.fov_radius}")

    def update_cooldown(self, value):
        self.cooldown_value_label.config(text=f"{float(value):.2f}")

    def update_fps(self, value):
        self.fps_value_label.config(text=f"{int(float(value))}")

    def toggle_detection(self):
        if self.running:
            self.running = False
            self.start_button.config(text="Start Detection")
            self.status_label.config(text="Status: Stopped", fg="#FF4500")
        else:
            self.running = True
            self.start_button.config(text="Stop Detection")
            self.status_label.config(text="Status: Running", fg="#32CD32")
            detection_thread = Thread(target=self.run_detection)
            detection_thread.daemon = True
            detection_thread.start()

    def run_detection(self):
        try:
            with mss() as sct:
                monitor = {
                    "top": self.center_y - self.fov_radius,
                    "left": self.center_x - self.fov_radius,
                    "width": self.fov_radius * 2,
                    "height": self.fov_radius * 2
                }

                fps = self.fps.get()
                sleep_time = 1 / fps

                while self.running:
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                    selected_color = self.selected_color.get().lower()
                    if selected_color == "yellow":
                        lower_color = np.array([0, 200, 200])
                        upper_color = np.array([100, 255, 255])
                    elif selected_color == "red":
                        lower_color = np.array([0, 0, 200])
                        upper_color = np.array([100, 100, 255])
                    elif selected_color == "purple":
                        lower_color = np.array([120, 0, 120])
                        upper_color = np.array([255, 100, 255])
                    else:
                        lower_color = np.array([0, 200, 200])
                        upper_color = np.array([100, 255, 255])

                    mask = cv2.inRange(frame, lower_color, upper_color)
                    color_detected = np.any(mask)

                    current_time = time.time()
                    cooldown = self.shot_cooldown.get()

                    if (
                        color_detected
                        and keyboard.is_pressed(self.activation_key.get())
                        and (current_time - self.last_shot_time) > cooldown
                    ):
                        keyboard.press_and_release(self.trigger_key.get())
                        self.last_shot_time = current_time

                    overlay = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
                    cv2.circle(overlay, (self.center_x, self.center_y), self.fov_radius, (0, 255, 0), 2)
                    if color_detected:
                        cv2.circle(overlay, (self.center_x, self.center_y), 10, (0, 255, 255), -1)
                    cv2.imshow("Overlay", overlay)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                    time.sleep(sleep_time)

                    if keyboard.is_pressed('insert'):
                        self.save_config()
                        self.running = False
                        self.root.quit()

        except Exception as e:
            pass
        finally:
            self.running = False
            self.start_button.config(text="Start Detection")
            self.status_label.config(text="Status: Stopped", fg="#FF4500")
            cv2.destroyAllWindows()

    def load_config(self):
        """Load configuration from JSON file or return default values."""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as file:
                return json.load(file)
        return {}

    def save_config(self):
        """Save current configuration to JSON file."""
        config = {
            "fov_radius": self.fov_radius,
            "selected_color": self.selected_color.get(),
            "trigger_key": self.trigger_key.get(),
            "activation_key": self.activation_key.get(),
            "shot_cooldown": self.shot_cooldown.get(),
            "fps": self.fps.get(),
        }
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file, indent=4)

    def on_close(self):
        """Save configuration before closing the application."""
        self.save_config()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorDetectorApp(root)
    root.mainloop()