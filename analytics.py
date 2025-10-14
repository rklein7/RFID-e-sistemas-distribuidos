#!/usr/bin/env python3
"""
Sistema de Análise de Dados com Pandas
Análise de logs de acesso ao sistema RFID
"""

import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Dict, List
import requests

# Configurações
DB_NAME = 'access_control.db'
API_URL = 'http://localhost:5000/api'
TOKEN = None  # Será configurado após login

class AccessAnalytics:
    def __init__(self, use_api=False, token=None):
        """
        Inicializa o sistema de análise
        
        Args:
            use_api: Se True, usa a API. Se False, acessa o banco diretamente.
            token: Token de autenticação para usar a API
        """
        self.use_api = use_api
        self.token = token
        self.df_logs = None
        self.df_collaborators = None
        
    def load_data_from_db(self):
        """Carrega dados diretamente do banco de dados"""
        conn = sqlite3.connect(DB_NAME)
        
        # Carregar logs
        query_logs = """
        SELECT 
            id,
            rfid_tag,
            collaborator_name,
            event_type,
            access_granted,
            timestamp,
            exit_timestamp
        FROM access_logs
        ORDER BY timestamp DESC
        """
        self.df_logs = pd.read_sql_query(query_logs, conn)
        
        # Converter timestamps
        self.df_logs['timestamp'] = pd.to_datetime(self.df_logs['timestamp'])
        self.df_logs['exit_timestamp'] = pd.to_datetime(self.df_logs['exit_timestamp'])
        
        # Carregar colaboradores
        query_collaborators = """
        SELECT 
            id,
            name,
            rfid_tag,
            has_access,
            created_at
        FROM collaborators
        """
        self.df_collaborators = pd.read_sql_query(query_collaborators, conn)
        self.df_collaborators['created_at'] = pd.to_datetime(self.df_collaborators['created_at'])
        
        conn.close()
        print(f"✅ Dados carregados: {len(self.df_logs)} logs, {len(self.df_collaborators)} colaboradores")
        
    def load_data_from_api(self):
        """Carrega dados via API"""
        if not self.token:
            raise ValueError("Token de autenticação não fornecido")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Carregar logs
        response = requests.get(f'{API_URL}/logs', headers=headers)
        if response.status_code == 200:
            logs_data = response.json()
            self.df_logs = pd.DataFrame(logs_data)
            self.df_logs['timestamp'] = pd.to_datetime(self.df_logs['timestamp'])
            self.df_logs['exit_timestamp'] = pd.to_datetime(self.df_logs['exit_timestamp'])
        else:
            raise Exception(f"Erro ao carregar logs: {response.status_code}")
        
        # Carregar colaboradores
        response = requests.get(f'{API_URL}/collaborators', headers=headers)
        if response.status_code == 200:
            collab_data = response.json()
            self.df_collaborators = pd.DataFrame(collab_data)
            self.df_collaborators['created_at'] = pd.to_datetime(self.df_collaborators['created_at'])
        else:
            raise Exception(f"Erro ao carregar colaboradores: {response.status_code}")
        
        print(f"✅ Dados carregados via API: {len(self.df_logs)} logs, {len(self.df_collaborators)} colaboradores")
    
    def load_data(self):
        """Carrega dados do banco ou API"""
        if self.use_api:
            self.load_data_from_api()
        else:
            self.load_data_from_db()
    
    def get_entries_exits_by_date(self, target_date: str) -> Dict:
        """
        Retorna quantas pessoas entraram e saíram em uma data específica
        
        Args:
            target_date: Data no formato 'YYYY-MM-DD'
        
        Returns:
            Dict com contagens de entradas e saídas
        """
        target = pd.to_datetime(target_date)
        
        # Filtrar eventos do dia
        mask_date = self.df_logs['timestamp'].dt.date == target.date()
        day_logs = self.df_logs[mask_date]
        
        # Contar entradas e saídas
        entries = len(day_logs[day_logs['event_type'] == 'entry'])
        exits = len(day_logs[day_logs['event_type'] == 'exit'])
        denied = len(day_logs[day_logs['event_type'] == 'denied'])
        unknown = len(day_logs[day_logs['event_type'] == 'unknown'])
        
        return {
            'date': target_date,
            'entries': entries,
            'exits': exits,
            'denied_access': denied,
            'invasion_attempts': unknown,
            'total_events': len(day_logs)
        }
    
    def get_collaborator_time_in_room(self, collaborator_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """
        Calcula o tempo total que um colaborador permaneceu na sala
        
        Args:
            collaborator_name: Nome do colaborador
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
        
        Returns:
            Dict com informações de tempo
        """
        # Filtrar logs do colaborador
        collab_logs = self.df_logs[self.df_logs['collaborator_name'] == collaborator_name].copy()
        
        # Aplicar filtro de datas se fornecido
        if start_date:
            collab_logs = collab_logs[collab_logs['timestamp'] >= pd.to_datetime(start_date)]
        if end_date:
            collab_logs = collab_logs[collab_logs['timestamp'] <= pd.to_datetime(end_date)]
        
        # Calcular tempo total
        total_seconds = 0
        sessions = []
        
        for _, row in collab_logs.iterrows():
            if row['event_type'] == 'entry' and pd.notna(row['exit_timestamp']):
                duration = (row['exit_timestamp'] - row['timestamp']).total_seconds()
                total_seconds += duration
                
                sessions.append({
                    'entry': row['timestamp'],
                    'exit': row['exit_timestamp'],
                    'duration_seconds': duration,
                    'duration_hours': duration / 3600
                })
        
        total_hours = total_seconds / 3600
        total_days = total_hours / 24
        
        return {
            'collaborator': collaborator_name,
            'total_seconds': total_seconds,
            'total_hours': round(total_hours, 2),
            'total_days': round(total_days, 2),
            'number_of_sessions': len(sessions),
            'sessions': sessions,
            'average_session_hours': round(total_hours / len(sessions), 2) if sessions else 0
        }
    
    def get_access_summary(self) -> pd.DataFrame:
        """Retorna resumo de acessos por colaborador"""
        summary = self.df_logs.groupby('collaborator_name').agg({
            'event_type': 'count',
            'access_granted': 'sum',
            'timestamp': ['min', 'max']
        }).reset_index()
        
        summary.columns = ['collaborator', 'total_events', 'successful_access', 'first_access', 'last_access']
        summary['failed_attempts'] = summary['total_events'] - summary['successful_access']
        
        return summary.sort_values('total_events', ascending=False)
    
    def get_hourly_distribution(self, target_date: Optional[str] = None) -> pd.DataFrame:
        """Retorna distribuição de acessos por hora do dia"""
        df = self.df_logs.copy()
        
        if target_date:
            target = pd.to_datetime(target_date)
            df = df[df['timestamp'].dt.date == target.date()]
        
        df['hour'] = df['timestamp'].dt.hour
        hourly = df.groupby(['hour', 'event_type']).size().reset_index(name='count')
        
        return hourly.pivot(index='hour', columns='event_type', values='count').fillna(0)
    
    def get_top_users_by_time(self, top_n: int = 10) -> pd.DataFrame:
        """Retorna os N colaboradores que mais permaneceram na sala"""
        results = []
        
        for name in self.df_logs['collaborator_name'].unique():
            if pd.notna(name) and name != 'Desconhecido':
                time_info = self.get_collaborator_time_in_room(name)
                results.append({
                    'collaborator': name,
                    'total_hours': time_info['total_hours'],
                    'sessions': time_info['number_of_sessions'],
                    'avg_session_hours': time_info['average_session_hours']
                })
        
        df_results = pd.DataFrame(results)
        return df_results.sort_values('total_hours', ascending=False).head(top_n)
    
    def get_security_alerts(self) -> pd.DataFrame:
        """Retorna alertas de segurança (tentativas negadas e invasões)"""
        alerts = self.df_logs[self.df_logs['event_type'].isin(['denied', 'unknown'])].copy()
        
        return alerts[['timestamp', 'rfid_tag', 'collaborator_name', 'event_type']].sort_values('timestamp', ascending=False)
    
    def generate_daily_report(self, target_date: str):
        """Gera relatório completo de um dia"""
        print("\n" + "="*70)
        print(f"📊 RELATÓRIO DIÁRIO - {target_date}")
        print("="*70)
        
        # Estatísticas do dia
        stats = self.get_entries_exits_by_date(target_date)
        print(f"\n📈 Estatísticas do Dia:")
        print(f"   • Entradas: {stats['entries']}")
        print(f"   • Saídas: {stats['exits']}")
        print(f"   • Acessos negados: {stats['denied_access']}")
        print(f"   • Tentativas de invasão: {stats['invasion_attempts']}")
        print(f"   • Total de eventos: {stats['total_events']}")
        
        # Distribuição por hora
        print(f"\n⏰ Distribuição por Hora:")
        hourly = self.get_hourly_distribution(target_date)
        if not hourly.empty:
            for hour in range(24):
                if hour in hourly.index:
                    entries = hourly.loc[hour, 'entry'] if 'entry' in hourly.columns else 0
                    if entries > 0:
                        print(f"   {hour:02d}:00 - {entries:.0f} entrada(s)")
        
        # Top usuários do dia
        print(f"\n👥 Colaboradores mais ativos:")
        target = pd.to_datetime(target_date)
        day_logs = self.df_logs[self.df_logs['timestamp'].dt.date == target.date()]
        
        if not day_logs.empty:
            top_users = day_logs[day_logs['event_type'] == 'entry'].groupby('collaborator_name').size().sort_values(ascending=False).head(5)
            for name, count in top_users.items():
                if pd.notna(name):
                    time_info = self.get_collaborator_time_in_room(name, target_date, target_date)
                    print(f"   • {name}: {count} entrada(s), {time_info['total_hours']:.2f}h no total")
        
        print("\n" + "="*70)
    
    def generate_full_report(self):
        """Gera relatório completo do sistema"""
        print("\n" + "="*70)
        print("📊 RELATÓRIO COMPLETO DO SISTEMA DE ACESSO")
        print("="*70)
        
        # Período analisado
        if not self.df_logs.empty:
            first_date = self.df_logs['timestamp'].min()
            last_date = self.df_logs['timestamp'].max()
            print(f"\n📅 Período: {first_date.strftime('%d/%m/%Y')} a {last_date.strftime('%d/%m/%Y')}")
        
        # Resumo geral
        print(f"\n📈 Resumo Geral:")
        print(f"   • Total de eventos: {len(self.df_logs)}")
        print(f"   • Colaboradores cadastrados: {len(self.df_collaborators)}")
        print(f"   • Acessos permitidos: {len(self.df_logs[self.df_logs['event_type'] == 'entry'])}")
        print(f"   • Acessos negados: {len(self.df_logs[self.df_logs['event_type'] == 'denied'])}")
        print(f"   • Tentativas de invasão: {len(self.df_logs[self.df_logs['event_type'] == 'unknown'])}")
        
        # Top usuários por tempo
        print(f"\n⏱️  Top 10 Colaboradores por Tempo na Sala:")
        top_users = self.get_top_users_by_time(10)
        for idx, row in top_users.iterrows():
            print(f"   {idx+1}. {row['collaborator']}: {row['total_hours']:.2f}h ({row['sessions']} sessões)")
        
        # Alertas de segurança
        alerts = self.get_security_alerts()
        print(f"\n⚠️  Alertas de Segurança (últimos 10):")
        if not alerts.empty:
            for _, alert in alerts.head(10).iterrows():
                timestamp = alert['timestamp'].strftime('%d/%m/%Y %H:%M')
                alert_type = "Acesso negado" if alert['event_type'] == 'denied' else "Tentativa de invasão"
                name = alert['collaborator_name'] if pd.notna(alert['collaborator_name']) else "Desconhecido"
                print(f"   • {timestamp} - {alert_type} - {name} ({alert['rfid_tag']})")
        else:
            print("   Nenhum alerta registrado")
        
        print("\n" + "="*70)

def main():
    """Função principal para demonstração"""
    print("🔐 Sistema de Análise de Dados - Controle de Acesso RFID\n")
    
    # Escolher método de acesso
    print("Escolha o método de acesso aos dados:")
    print("1 - Banco de dados local (direto)")
    print("2 - API REST (requer autenticação)")
    choice = input("\nOpção: ").strip()
    
    if choice == '2':
        # Login na API
        username = input("Usuário: ")
        password = input("Senha: ")
        
        response = requests.post(f'{API_URL}/auth/login', json={
            'username': username,
            'password': password
        })
        
        if response.status_code == 200:
            token = response.json()['token']
            analytics = AccessAnalytics(use_api=True, token=token)
        else:
            print("❌ Falha na autenticação")
            return
    else:
        analytics = AccessAnalytics(use_api=False)
    
    # Carregar dados
    analytics.load_data()
    
    # Menu interativo
    while True:
        print("\n" + "="*70)
        print("MENU DE ANÁLISES")
        print("="*70)
        print("1 - Relatório completo do sistema")
        print("2 - Relatório de um dia específico")
        print("3 - Tempo de permanência de um colaborador")
        print("4 - Top usuários por tempo na sala")
        print("5 - Alertas de segurança")
        print("6 - Resumo de acessos por colaborador")
        print("0 - Sair")
        
        option = input("\nEscolha uma opção: ").strip()
        
        if option == '1':
            analytics.generate_full_report()
        
        elif option == '2':
            date = input("Digite a data (YYYY-MM-DD): ").strip()
            analytics.generate_daily_report(date)
        
        elif option == '3':
            name = input("Digite o nome do colaborador: ").strip()
            result = analytics.get_collaborator_time_in_room(name)
            print(f"\n⏱️  Tempo de permanência de {name}:")
            print(f"   • Total: {result['total_hours']:.2f} horas ({result['total_days']:.2f} dias)")
            print(f"   • Número de sessões: {result['number_of_sessions']}")
            print(f"   • Média por sessão: {result['average_session_hours']:.2f} horas")
        
        elif option == '4':
            top = analytics.get_top_users_by_time(10)
            print("\n⏱️  Top 10 Usuários por Tempo na Sala:")
            print(top.to_string(index=False))
        
        elif option == '5':
            alerts = analytics.get_security_alerts()
            print("\n⚠️  Alertas de Segurança:")
            if not alerts.empty:
                print(alerts.head(20).to_string(index=False))
            else:
                print("Nenhum alerta registrado")
        
        elif option == '6':
            summary = analytics.get_access_summary()
            print("\n📊 Resumo de Acessos por Colaborador:")
            print(summary.to_string(index=False))
        
        elif option == '0':
            print("\n👋 Encerrando sistema. Até logo!")
            break
        
        else:
            print("❌ Opção inválida!")

if __name__ == '__main__':
    main()