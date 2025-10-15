import React, { useState, useEffect } from 'react';
import { Shield, Users, Activity, AlertTriangle, Clock, UserCheck, UserX, LogIn, LogOut } from 'lucide-react';

const API_URL = 'http://localhost:5000/api';

const Dashboard = () => {
  const [token, setToken] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [events, setEvents] = useState([]);
  const [collaborators, setCollaborators] = useState([]);
  const [stats, setStats] = useState({
    totalAccess: 0,
    deniedAccess: 0,
    invasionAttempts: 0,
    currentInside: 0
  });
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', rfid_tag: '', has_access: true });
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    if (token) {
      loadCollaborators();
      loadLogs();
      const interval = setInterval(() => {
        loadLogs();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [token]);

  const loadCollaborators = async () => {
    try {
      const response = await fetch(`${API_URL}/collaborators`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCollaborators(data);
      }
    } catch (error) {
      console.error('Erro ao carregar colaboradores:', error);
    }
  };

  const loadLogs = async () => {
    try {
      const response = await fetch(`${API_URL}/logs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setEvents(data.slice(0, 20));
        
        const newStats = {
          totalAccess: data.filter(e => e.event_type === 'entry' && e.access_granted).length,
          deniedAccess: data.filter(e => e.event_type === 'denied').length,
          invasionAttempts: data.filter(e => e.event_type === 'unknown').length,
          currentInside: data.filter(e => e.event_type === 'entry' && !e.exit_timestamp).length
        };
        setStats(newStats);
      }
    } catch (error) {
      console.error('Erro ao carregar logs:', error);
    }
  };

  const handleLogin = async () => {
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      const data = await response.json();
      if (response.ok) {
        setToken(data.token);
      } else {
        alert('Credenciais inválidas');
      }
    } catch (error) {
      alert('Erro ao conectar com o servidor');
    }
  };

  const logout = () => {
    setToken('');
    setUsername('');
    setPassword('');
  };

  const createCollaborator = async () => {
    try {
      const response = await fetch(`${API_URL}/collaborators`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editForm)
      });
      
      if (response.ok) {
        loadCollaborators();
        setShowAddForm(false);
        setEditForm({ name: '', rfid_tag: '', has_access: true });
      } else {
        const data = await response.json();
        alert(data.error || 'Erro ao criar colaborador');
      }
    } catch (error) {
      alert('Erro ao conectar com o servidor');
    }
  };

  const updateCollaborator = async (id, updates) => {
    try {
      const response = await fetch(`${API_URL}/collaborators/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      });
      
      if (response.ok) {
        loadCollaborators();
      }
    } catch (error) {
      console.error('Erro ao atualizar colaborador:', error);
    }
  };

  const deleteCollaborator = async (id) => {
    if (!window.confirm('Deseja realmente excluir este colaborador?')) return;
    
    try {
      const response = await fetch(`${API_URL}/collaborators/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        loadCollaborators();
      }
    } catch (error) {
      console.error('Erro ao excluir colaborador:', error);
    }
  };

  const getEventIcon = (eventType, accessGranted) => {
    if (eventType === 'entry') return <LogIn className="w-5 h-5 text-green-500" />;
    if (eventType === 'exit') return <LogOut className="w-5 h-5 text-blue-500" />;
    if (eventType === 'denied') return <UserX className="w-5 h-5 text-orange-500" />;
    if (eventType === 'unknown') return <AlertTriangle className="w-5 h-5 text-red-500" />;
    return <Activity className="w-5 h-5 text-gray-500" />;
  };

  const getEventText = (event) => {
    if (event.event_type === 'entry') return `${event.collaborator_name} entrou na sala`;
    if (event.event_type === 'exit') return `${event.collaborator_name} saiu da sala`;
    if (event.event_type === 'denied') return `Acesso negado para ${event.collaborator_name}`;
    if (event.event_type === 'unknown') return `Tentativa de invasão detectada (Tag: ${event.rfid_tag})`;
    return 'Evento desconhecido';
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString('pt-BR');
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
        <div className="bg-slate-800 rounded-2xl shadow-2xl p-8 w-full max-w-md border border-slate-700">
          <div className="flex items-center justify-center mb-8">
            <Shield className="w-16 h-16 text-blue-400" />
          </div>
          <h1 className="text-3xl font-bold text-white text-center mb-2">Sistema de Segurança</h1>
          <p className="text-slate-400 text-center mb-8">Monitoramento de Acesso em Tempo Real</p>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Usuário</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Digite seu usuário"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Senha</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Digite sua senha"
              />
            </div>
            
            <button
              onClick={handleLogin}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors duration-200"
            >
              Entrar
            </button>
          </div>
          
          <p className="text-slate-500 text-sm text-center mt-6">
            Credenciais padrão: admin / admin123
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-3">
            <Shield className="w-10 h-10 text-blue-400" />
            <div>
              <h1 className="text-3xl font-bold text-white">Sistema de Segurança</h1>
              <p className="text-slate-400">Monitoramento em Tempo Real</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Sair
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <UserCheck className="w-8 h-8 text-green-400" />
              <span className="text-3xl font-bold text-white">{stats.totalAccess}</span>
            </div>
            <p className="text-slate-400">Acessos Permitidos</p>
          </div>
          
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <Users className="w-8 h-8 text-blue-400" />
              <span className="text-3xl font-bold text-white">{stats.currentInside}</span>
            </div>
            <p className="text-slate-400">Pessoas na Sala</p>
          </div>
          
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <UserX className="w-8 h-8 text-orange-400" />
              <span className="text-3xl font-bold text-white">{stats.deniedAccess}</span>
            </div>
            <p className="text-slate-400">Acessos Negados</p>
          </div>
          
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <AlertTriangle className="w-8 h-8 text-red-400" />
              <span className="text-3xl font-bold text-white">{stats.invasionAttempts}</span>
            </div>
            <p className="text-slate-400">Tentativas de Invasão</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center gap-2 mb-6">
              <Activity className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-semibold text-white">Atividades Recentes</h2>
            </div>
            
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {events.length === 0 ? (
                <p className="text-slate-500 text-center py-8">Nenhuma atividade registrada</p>
              ) : (
                events.map((event, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-slate-700 rounded-lg">
                    {getEventIcon(event.event_type, event.access_granted)}
                    <div className="flex-1">
                      <p className="text-white">{getEventText(event)}</p>
                      <p className="text-sm text-slate-400 mt-1">
                        {formatTimestamp(event.timestamp)}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Users className="w-6 h-6 text-blue-400" />
                <h2 className="text-xl font-semibold text-white">Colaboradores</h2>
              </div>
              <button
                onClick={() => setShowAddForm(!showAddForm)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
              >
                {showAddForm ? 'Cancelar' : '+ Adicionar'}
              </button>
            </div>

            {showAddForm && (
              <div className="mb-6 p-4 bg-slate-700 rounded-lg space-y-3">
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({...editForm, name: e.target.value})}
                  placeholder="Nome completo"
                  className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white text-sm"
                />
                <input
                  type="text"
                  value={editForm.rfid_tag}
                  onChange={(e) => setEditForm({...editForm, rfid_tag: e.target.value})}
                  placeholder="Tag RFID (ex: RFID001)"
                  className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white text-sm"
                />
                <label className="flex items-center gap-2 text-white text-sm">
                  <input
                    type="checkbox"
                    checked={editForm.has_access}
                    onChange={(e) => setEditForm({...editForm, has_access: e.target.checked})}
                    className="rounded"
                  />
                  Tem permissão de acesso
                </label>
                <button
                  onClick={createCollaborator}
                  className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors"
                >
                  Criar Colaborador
                </button>
              </div>
            )}
            
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {collaborators.map((collab) => (
                <div key={collab.id} className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
                  <div className="flex-1">
                    <p className="text-white font-medium">{collab.name}</p>
                    <p className="text-sm text-slate-400">{collab.rfid_tag}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => updateCollaborator(collab.id, { has_access: !collab.has_access })}
                      className={`px-3 py-1 rounded text-xs font-medium ${
                        collab.has_access 
                          ? 'bg-green-600 text-white' 
                          : 'bg-red-600 text-white'
                      }`}
                    >
                      {collab.has_access ? 'Autorizado' : 'Bloqueado'}
                    </button>
                    <button
                      onClick={() => deleteCollaborator(collab.id)}
                      className="px-3 py-1 bg-red-700 hover:bg-red-800 text-white rounded text-xs transition-colors"
                    >
                      Excluir
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;