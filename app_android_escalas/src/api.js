/*
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: app_android_escalas/src/api.js
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
*/
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Como o apk vai rodar no android, e o django localmente no pc
// Usamos o IP da maquina na rede, ou se for emulador, 10.0.2.2.
// Altere para o IP de producao quando fizer deploy.
export const BASE_URL = 'http://192.168.1.9:8000/api';

const api = axios.create({
  baseURL: BASE_URL,
});

api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;
