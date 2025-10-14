#!/usr/bin/env python3
"""
Sistema de Controle de Acesso RFID para Raspberry Pi
Requisitos: pip install RPi.GPIO mfrc522 requests
"""

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import requests
from datetime import datetime, timedelta
import signal
import sys

# Configurações
API_URL = 'http://localhost:5000/api'  # Alterar para IP do servidor
LED_GREEN_PIN = 17  # GPIO 17
LED_RED_PIN = 27    # GPIO 27

# Cache local de colaboradores
collaborators_cache = {}
cache_last_update = None
CACHE_REFRESH_INTERVAL = 300  # 5 minutos

# Controle de presença
presence_control = {}  # {rfid_tag: {'name': str, 'entry_time': datetime, 'is_inside': bool}}

# Estatísticas da sessão
session_stats = {
    'access_attempts': {},  # {name: count} para não autorizados
    'invasion_attempts': 0,
    'time_in_room': {}  # {name: total_seconds}
}

class RFIDAccessControl:
    def __init__(self):
        self.reader = SimpleMFRC522()
        self.setup_gpio()
        self.running = True
        
    def setup_gpio(self):
        """Configura os pinos GPIO"""
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LED_GREEN_PIN, GPIO.OUT)
        GPIO.setup(LED_RED_PIN, GPIO.OUT)
        GPIO.output(LED_GREEN_PIN, GPIO.LOW)
        GPIO.output(LED_RED_PIN, GPIO.LOW)
        
    def cleanup(self):
        """Limpa recursos GPIO"""
        GPIO.cleanup()
        
    def blink_led(self, pin, times=1, duration=0.5):
        """Pisca um LED"""
        for _ in range(times):
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(pin, GPIO.LOW)
            if times > 1:
                time.sleep(duration)
    
    def activate_led(self, pin, duration=5):
        """Ativa LED por um período"""
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(pin, GPIO.LOW)
        
    def update_cache(self):
        """Atualiza cache de colaboradores da API"""
        global collaborators_cache, cache_last_update
        
        try:
            response = requests.get(f'{API_URL}/rfid/collaborators', timeout=5)
            if response.status_code == 200:
                collaborators_cache = response.json()
                cache_last_update = datetime.now()
                print(f'✅ Cache atualizado: {len(collaborators_cache)} colaboradores')
                return True
        except requests.exceptions.RequestException as e:
            print(f'⚠️  Erro ao atualizar cache: {e}')
            if not collaborators_cache:
                print('❌ Sistema funcionando em modo offline (cache vazio)')
        
        return False
    
    def should_refresh_cache(self):
        """Verifica se deve atualizar o cache"""
        if not cache_last_update:
            return True
        
        elapsed = (datetime.now() - cache_last_update).total_seconds()
        return elapsed >= CACHE_REFRESH_INTERVAL
    
    def log_to_api(self, rfid_tag, collaborator_name, event_type, access_granted):
        """Registra log na API"""
        try:
            data = {
                'rfid_tag': rfid_tag,
                'collaborator_name': collaborator_name,
                'event_type': event_type,
                'access_granted': access_granted
            }
            requests.post(f'{API_URL}/logs/access', json=data, timeout=3)
        except requests.exceptions.RequestException:
            print('⚠️  Não foi possível registrar log na API')
    
    def handle_entry(self, rfid_tag, name, is_first_entry):
        """Gerencia entrada autorizada"""
        if is_first_entry:
            print(f'\n✅ Bem-vindo, {name}')
        else:
            print(f'\n✅ Bem-vindo de volta, {name}')
        
        presence_control[rfid_tag] = {
            'name': name,
            'entry_time': datetime.now(),
            'is_inside': True
        }
        
        self.activate_led(LED_GREEN_PIN, 5)
        self.log_to_api(rfid_tag, name, 'entry', True)
    
    def handle_exit(self, rfid_tag, name):
        """Gerencia saída"""
        print(f'\n👋 Até logo, {name}')
        
        entry_time = presence_control[rfid_tag]['entry_time']
        exit_time = datetime.now()
        duration = (exit_time - entry_time).total_seconds()
        
        # Atualizar tempo total
        if name not in session_stats['time_in_room']:
            session_stats['time_in_room'][name] = 0
        session_stats['time_in_room'][name] += duration
        
        presence_control[rfid_tag]['is_inside'] = False
        
        self.activate_led(LED_GREEN_PIN, 2)
        self.log_to_api(rfid_tag, name, 'exit', True)
        
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        print(f'⏱️  Tempo nesta sessão: {hours}h {minutes}min')
    
    def handle_denied_access(self, rfid_tag, name):
        """Gerencia acesso negado"""
        print(f'\n❌ Você não tem acesso a este projeto, {name}')
        
        if name not in session_stats['access_attempts']:
            session_stats['access_attempts'][name] = 0
        session_stats['access_attempts'][name] += 1
        
        self.activate_led(LED_RED_PIN, 5)
        self.log_to_api(rfid_tag, name, 'denied', False)
    
    def handle_unknown_tag(self, rfid_tag):
        """Gerencia tag desconhecida (tentativa de invasão)"""
        print(f'\n⚠️  Identificação não encontrada!')
        print(f'🔴 ALERTA: Possível tentativa de invasão! Tag: {rfid_tag}')
        
        session_stats['invasion_attempts'] += 1
        
        self.blink_led(LED_RED_PIN, times=10, duration=0.5)
        self.log_to_api(rfid_tag, 'Desconhecido', 'unknown', False)
    
    def process_rfid_tag(self, rfid_tag):
        """Processa leitura de tag RFID"""
        # Atualizar cache se necessário
        if self.should_refresh_cache():
            self.update_cache()
        
        # Verificar se tag existe no cache
        if rfid_tag not in collaborators_cache:
            self.handle_unknown_tag(rfid_tag)
            return
        
        collaborator = collaborators_cache[rfid_tag]
        name = collaborator['name']
        has_access = collaborator['has_access']
        
        # Verificar autorização
        if not has_access:
            self.handle_denied_access(rfid_tag, name)
            return
        
        # Verificar se está entrando ou saindo
        is_inside = presence_control.get(rfid_tag, {}).get('is_inside', False)
        
        if is_inside:
            # Saída
            self.handle_exit(rfid_tag, name)
        else:
            # Entrada
            is_first_entry = rfid_tag not in presence_control
            self.handle_entry(rfid_tag, name, is_first_entry)
    
    def print_session_report(self):
        """Imprime relatório da sessão"""
        print('\n' + '='*70)
        print('📊 RELATÓRIO DE ATIVIDADES DA SESSÃO')
        print('='*70)
        
        # Tempo de permanência
        print('\n⏱️  TEMPO DE PERMANÊNCIA NA SALA:')
        if session_stats['time_in_room']:
            for name, total_seconds in session_stats['time_in_room'].items():
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                print(f'   • {name}: {hours}h {minutes}min {seconds}s')
        else:
            print('   Nenhum registro de permanência')
        
        # Tentativas de acesso negado
        print('\n🚫 TENTATIVAS DE ACESSO NÃO AUTORIZADO:')
        if session_stats['access_attempts']:
            for name, count in session_stats['access_attempts'].items():
                print(f'   • {name}: {count} tentativa(s)')
        else:
            print('   Nenhuma tentativa registrada')
        
        # Tentativas de invasão
        print(f'\n⚠️  TENTATIVAS DE INVASÃO: {session_stats["invasion_attempts"]}')
        
        # Pessoas atualmente na sala
        print('\n👥 PESSOAS ATUALMENTE NA SALA:')
        inside_count = 0
        for tag, data in presence_control.items():
            if data.get('is_inside'):
                inside_count += 1
                entry_time = data['entry_time']
                duration = (datetime.now() - entry_time).total_seconds()
                hours = int(duration // 3600)
                minutes = int((duration % 3600) // 60)
                print(f'   • {data["name"]} (há {hours}h {minutes}min)')
        
        if inside_count == 0:
            print('   Sala vazia')
        
        print('\n' + '='*70)
        print('Sistema encerrado. Até logo! 👋')
        print('='*70 + '\n')
    
    def run(self):
        """Loop principal"""
        print('\n' + '='*70)
        print('🔐 SISTEMA DE CONTROLE DE ACESSO RFID')
        print('='*70)
        print('Inicializando...')
        
        # Atualizar cache inicial
        if not self.update_cache():
            print('⚠️  Aviso: Sistema iniciado sem conexão com API')
        
        print('\n✅ Sistema pronto! Aguardando leitura de tags...')
        print('Pressione Ctrl+C para encerrar\n')
        
        last_tag = None
        last_read_time = None
        DEBOUNCE_TIME = 3  # segundos
        
        try:
            while self.running:
                # Ler tag RFID
                tag_id, text = self.reader.read()
                
                if tag_id:
                    rfid_tag = f'RFID{tag_id:03d}'
                    current_time = time.time()
                    
                    # Debounce: ignorar leituras repetidas muito rápidas
                    if last_tag == rfid_tag and last_read_time:
                        if (current_time - last_read_time) < DEBOUNCE_TIME:
                            continue
                    
                    last_tag = rfid_tag
                    last_read_time = current_time
                    
                    print(f'\n🔍 Tag detectada: {rfid_tag}')
                    self.process_rfid_tag(rfid_tag)
                    print('\nAguardando próxima leitura...')
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print('\n\n⏹️  Encerrando sistema...')
            self.running = False
    
    def shutdown(self):
        """Encerra sistema e exibe relatório"""
        self.print_session_report()
        self.cleanup()

def signal_handler(sig, frame):
    """Gerencia sinal de interrupção"""
    if 'control' in globals():
        control.shutdown()
    sys.exit(0)

if __name__ == '__main__':
    # Configurar handler de sinal
    signal.signal(signal.SIGINT, signal_handler)
    
    # Inicializar sistema
    control = RFIDAccessControl()
    
    try:
        control.run()
    except Exception as e:
        print(f'\n❌ Erro fatal: {e}')
        control.shutdown()
        sys.exit(1)