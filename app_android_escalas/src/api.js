import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Como o apk vai rodar no android, e o django localmente no pc
// Usamos o IP da maquina na rede, ou se for emulador, 10.0.2.2.
// Altere para o IP de producao quando fizer deploy.
export const BASE_URL = 'http://10.0.2.2:8000/api';

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
