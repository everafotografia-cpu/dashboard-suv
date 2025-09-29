import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import threading
import requests

def create_github_repo(github_user, token):
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": "dashboard-suv",
        "description": "Dashboard de SUVs México 2026",
        "private": False,
        "auto_init": True
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        return True, "✅ Repositorio creado con éxito."
    elif response.status_code == 422:
        return True, "⚠️ El repositorio ya existe."  # Ya está creado
    else:
        return False, f"❌ Error al crear repositorio: {response.json().get('message', 'Desconocido')}"

def run_git_commands(project_path, github_user, token):
    try:
        os.chdir(project_path)

        # Crear repositorio si no existe
        success, msg = create_github_repo(github_user, token)
        if not success:
            return False, msg

        # Inicializar repo si no existe
        if not os.path.exists(".git"):
            subprocess.run(["git", "init"], check=True, capture_output=True)

        # Verificar si hay cambios
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            return True, "✅ No hay cambios. Todo está actualizado."

        # Configurar nombre y email
        subprocess.run(["git", "config", "user.name", github_user], check=True)
        subprocess.run(["git", "config", "user.email", f"{github_user}@users.noreply.github.com"], check=True)

        # Agregar y hacer commit
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Actualización automática del dashboard"], check=True, capture_output=True)

        # Configurar remote
        remote_url = f"https://{github_user}:{token}@github.com/{github_user}/dashboard-suv.git"
        result = subprocess.run(["git", "remote"], capture_output=True, text=True)
        if "origin" not in result.stdout:
            subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
        else:
            subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)

        # Subir cambios
        subprocess.run(["git", "branch", "-M", "main"], check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True, capture_output=True)

        return True, f"✅ ¡Actualizado con éxito!\nURL: https://{github_user}.github.io/dashboard-suv/"

    except subprocess.CalledProcessError as e:
        return False, f"❌ Error de Git:\n{e.stderr or str(e)}"
    except Exception as e:
        return False, f"❌ Error inesperado:\n{str(e)}"

def deploy():
    project_path = entry_path.get()
    github_user = entry_user.get()
    token = entry_token.get()

    if not project_path or not github_user or not token:
        messagebox.showerror("Error", "Por favor llena todos los campos.")
        return

    if not os.path.exists(os.path.join(project_path, "index.html")):
        messagebox.showerror("Error", "La carpeta debe contener 'index.html'")
        return

    def task():
        btn_deploy.config(state="disabled")
        progress.grid(row=5, column=0, columnspan=3, pady=10)
        progress.start()

        success, message = run_git_commands(project_path, github_user, token)

        progress.stop()
        progress.grid_forget()
        btn_deploy.config(state="normal")

        if success:
            messagebox.showinfo("Éxito", message)
        else:
            messagebox.showerror("Error", message)

    threading.Thread(target=task, daemon=True).start()

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, folder)

# === Interfaz gráfica ===
root = tk.Tk()
root.title("🔄 Actualizar Dashboard en GitHub Pages")
root.geometry("520x320")
root.resizable(False, False)

tk.Label(root, text="Ruta del proyecto (carpeta dashboard-suv):").grid(row=0, column=0, sticky="w", padx=20, pady=(20,5))
entry_path = tk.Entry(root, width=50)
entry_path.grid(row=1, column=0, padx=20, pady=5)
tk.Button(root, text="Buscar", command=browse_folder).grid(row=1, column=1, padx=10)

tk.Label(root, text="Usuario de GitHub:").grid(row=2, column=0, sticky="w", padx=20, pady=(15,5))
entry_user = tk.Entry(root, width=40)
entry_user.grid(row=3, column=0, padx=20, pady=5)

tk.Label(root, text="Token de GitHub (Classic):").grid(row=4, column=0, sticky="w", padx=20, pady=(15,5))
entry_token = tk.Entry(root, width=40, show="*")
entry_token.grid(row=5, column=0, padx=20, pady=5)

btn_deploy = tk.Button(
    root,
    text="🔄 Actualizar en GitHub Pages",
    command=deploy,
    bg="#3498db",
    fg="white",
    font=("Arial", 10, "bold"),
    height=2
)
btn_deploy.grid(row=6, column=0, pady=20)

progress = ttk.Progressbar(root, mode="indeterminate", length=300)

root.mainloop()