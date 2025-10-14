#!/usr/bin/env python3
"""
Simulador de Testes para Sistema de Controle de Acesso RFID
Simula leituras de tags sem necessidade de hardware físico
"""

import requests
import time
import random
from datetime import datetime
from typing import Dict, List

API_URL = 'http://localhost:5000/api'

class RFIDSimulator:
    """Simulador de leituras RFID para testes"""
    
    def __init__(self):
        self.collaborators = {}
        self.presence_control = {}
        self.load_collaborators()
        
    def load_collaborators(self):
        """Carrega colaboradores da API"""
        try:
            response = requests.get(f'{API_URL}/rfid/collaborators', timeout=5)
            if response.status_code == 200:
                self.collaborators = response.json()
                print(f'✅ {len(self.collaborators)} colaboradores carregados')
                return True
        except requests.exceptions.RequestException as e:
            print(f'⚠️  Erro ao carregar colaboradores: {e}')
            # Criar dados de exemplo para testes offline
            self.collaborators = {
                'RFID001': {'name': 'João Silva', 'has_access': True},
                'RFID002': {'name': 'Maria Santos', 'has_access': True},
                'RFID003': {'name': 'Pedro Oliveira', 'has_access': False},
                'RFID004': {'name': 'Ana Costa', 'has_access': True},
            }
            print(f'⚠️  Usando dados de exemplo offline')
        return False
    
    def log_to_api(self, rfid_tag, collaborator_name, event_type, access_granted):
        """Registra log na API"""
        try:
            data = {
                'rfid_tag': rfid_tag,
                'collaborator_name': collaborator_name,
                'event_type': event_type,
                'access_granted': access_granted
            }
            response = requests.post(f'{API_URL}/logs/access', json=data, timeout=3)
            return response.status_code == 201
        except requests.exceptions.RequestException:
            return False
    
    def simulate_read(self, rfid_tag: str, verbose=True):
        """Simula leitura de uma tag RFID"""
        if verbose:
            print(f'\n🔍 Tag detectada: {rfid_tag}')
        
        # Verificar se tag existe
        if rfid_tag not in self.collaborators:
            if verbose:
                print(f'⚠️  Identificação não encontrada!')
                print(f'🔴 ALERTA: Possível tentativa de invasão!')
            self.log_to_api(rfid_tag, 'Desconhecido', 'unknown', False)
            return 'unknown'
        
        collaborator = self.collaborators[rfid_tag]
        name = collaborator['name']
        has_access = collaborator['has_access']
        
        # Verificar autorização
        if not has_access:
            if verbose:
                print(f'❌ Você não tem acesso a este projeto, {name}')
            self.log_to_api(rfid_tag, name, 'denied', False)
            return 'denied'
        
        # Verificar se está entrando ou saindo
        is_inside = self.presence_control.get(rfid_tag, {}).get('is_inside', False)
        
        if is_inside:
            # Saída
            if verbose:
                print(f'👋 Até logo, {name}')
            self.presence_control[rfid_tag]['is_inside'] = False
            self.log_to_api(rfid_tag, name, 'exit', True)
            return 'exit'
        else:
            # Entrada
            is_first_entry = rfid_tag not in self.presence_control
            
            if is_first_entry:
                if verbose:
                    print(f'✅ Bem-vindo, {name}')
            else:
                if verbose:
                    print(f'✅ Bem-vindo de volta, {name}')
            
            self.presence_control[rfid_tag] = {
                'name': name,
                'is_inside': True,
                'entry_time': datetime.now()
            }
            
            self.log_to_api(rfid_tag, name, 'entry', True)
            return 'entry'
    
    def simulate_scenario(self, scenario_name: str):
        """Simula cenários pré-definidos de teste"""
        print(f'\n{"="*70}')
        print(f'🎬 SIMULAÇÃO: {scenario_name}')
        print(f'{"="*70}')
        
        if scenario_name == 'dia_normal':
            self._scenario_normal_day()
        elif scenario_name == 'tentativas_invasao':
            self._scenario_invasion_attempts()
        elif scenario_name == 'acesso_negado':
            self._scenario_denied_access()
        elif scenario_name == 'stress_test':
            self._scenario_stress_test()
        else:
            print('❌ Cenário não encontrado')
    
    def _scenario_normal_day(self):
        """Simula um dia normal de trabalho"""
        print('\n📅 Simulando dia normal de trabalho...\n')
        
        # Manhã - Chegadas
        print('🌅 08:00 - Chegadas da manhã')
        for tag in ['RFID001', 'RFID002', 'RFID004']:
            self.simulate_read(tag)
            time.sleep(1)
        
        time.sleep(2)
        
        # Saída para almoço
        print('\n🍽️  12:00 - Saída para almoço')
        for tag in ['RFID001', 'RFID002']:
            self.simulate_read(tag)
            time.sleep(1)
        
        time.sleep(2)
        
        # Retorno do almoço
        print('\n🔙 13:00 - Retorno do almoço')
        for tag in ['RFID001', 'RFID002']:
            self.simulate_read(tag)
            time.sleep(1)
        
        time.sleep(2)
        
        # Fim do expediente
        print('\n🌆 18:00 - Saídas do fim do dia')
        for tag in ['RFID001', 'RFID002', 'RFID004']:
            self.simulate_read(tag)
            time.sleep(1)
        
        print('\n✅ Simulação de dia normal concluída!')
    
    def _scenario_invasion_attempts(self):
        """Simula tentativas de invasão"""
        print('\n🚨 Simulando tentativas de invasão...\n')
        
        fake_tags = ['RFID999', 'RFID888', 'RFID777']
        
        for i, tag in enumerate(fake_tags, 1):
            print(f'\nTentativa {i}:')
            self.simulate_read(tag)
            time.sleep(2)
        
        print('\n✅ Simulação de tentativas de invasão concluída!')
    
    def _scenario_denied_access(self):
        """Simula tentativas de acesso negado"""
        print('\n🚫 Simulando acessos negados...\n')
        
        # Pedro Oliveira não tem acesso
        for i in range(3):
            print(f'\nTentativa {i+1}:')
            self.simulate_read('RFID003')
            time.sleep(2)
        
        print('\n✅ Simulação de acessos negados concluída!')
    
    def _scenario_stress_test(self):
        """Simula múltiplos acessos simultâneos"""
        print('\n⚡ Simulando teste de stress (50 eventos)...\n')
        
        authorized_tags = ['RFID001', 'RFID002', 'RFID004']
        
        for i in range(50):
            tag = random.choice(authorized_tags)
            result = self.simulate_read(tag, verbose=False)
            
            status = {
                'entry': '✅ Entrada',
                'exit': '👋 Saída',
                'denied': '❌ Negado',
                'unknown': '⚠️ Invasão'
            }
            
            print(f'{i+1:3d}. {tag} - {status.get(result, "?")}')
            time.sleep(0.3)
        
        print('\n✅ Teste de stress concluído!')
    
    def interactive_mode(self):
        """Modo interativo de simulação"""
        print('\n{"="*70}')
        print('🎮 MODO INTERATIVO - SIMULADOR RFID')
        print('="*70}')
        print('\nDigite uma tag RFID ou comando:')
        print('  - RFID001, RFID002, RFID003, RFID004 (tags cadastradas)')
        print('  - RFIDxxx (qualquer outra tag - teste de invasão)')
        print('  - "reload" - recarregar colaboradores')
        print('  - "status" - ver quem está na sala')
        print('  - "exit" - sair\n')
        
        while True:
            try:
                command = input('Tag ou comando: ').strip()
                
                if not command:
                    continue
                
                if command.lower() == 'exit':
                    print('\n👋 Encerrando simulador...')
                    break
                
                if command.lower() == 'reload':
                    self.load_collaborators()
                    continue
                
                if command.lower() == 'status':
                    print('\n👥 Pessoas na sala:')
                    inside_count = 0
                    for tag, data in self.presence_control.items():
                        if data.get('is_inside'):
                            inside_count += 1
                            print(f'   • {data["name"]} (Tag: {tag})')
                    if inside_count == 0:
                        print('   Sala vazia')
                    print()
                    continue
                
                # Simular leitura da tag
                self.simulate_read(command.upper())
                
            except KeyboardInterrupt:
                print('\n\n👋 Encerrando simulador...')
                break
            except Exception as e:
                print(f'❌ Erro: {e}')

def main():
    """Função principal"""
    simulator = RFIDSimulator()
    
    print('\n🔐 SIMULADOR DE TESTES - SISTEMA RFID')
    print('='*70)
    print('\nEscolha o modo de simulação:')
    print('1 - Modo Interativo (leitura manual de tags)')
    print('2 - Cenário: Dia Normal de Trabalho')
    print('3 - Cenário: Tentativas de Invasão')
    print('4 - Cenário: Acessos Negados')
    print('5 - Cenário: Teste de Stress')
    print('0 - Sair')
    
    choice = input('\nOpção: ').strip()
    
    if choice == '1':
        simulator.interactive_mode()
    elif choice == '2':
        simulator.simulate_scenario('dia_normal')
    elif choice == '3':
        simulator.simulate_scenario('tentativas_invasao')
    elif choice == '4':
        simulator.simulate_scenario('acesso_negado')
    elif choice == '5':
        simulator.simulate_scenario('stress_test')
    elif choice == '0':
        print('\n👋 Até logo!')
    else:
        print('❌ Opção inválida!')

if __name__ == '__main__':
    main()