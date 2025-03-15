import axios from 'axios';

const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Интерцептор для добавления авторизации
api.interceptors.request.use(config => {
  if (window.Telegram?.WebApp) {
    const webApp = window.Telegram.WebApp;
    const authData = {
      id: webApp.initDataUnsafe?.user?.id
    };
    
    if (authData.id) {
      config.headers.Authorization = JSON.stringify(authData);
    }
  }
  return config;
});

export default api;

// Функции для работы с API
export const banUser = async (formData) => {
  try {
    const response = await api.post('/USFAPI/banuser', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error banning user:', error);
    throw error;
  }
};

export const getUserInfo = async (userId) => {
  try {
    const response = await api.get(`/USFAPI/user/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting user info:', error);
    throw error;
  }
};

export const checkAdmin = async (userId) => {
  try {
    const response = await api.get(`/check_admin/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Error checking admin:', error);
    throw error;
  }
};

export const muteUser = async (formData) => {
  try {
    const response = await api.post('/USFAPI/mute', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error muting user:', error);
    throw error;
  }
};

export const getBans = async (searchId = null) => {
  try {
    const params = searchId ? { search_id: searchId } : {};
    const response = await api.get('/USFAPI/bans', { params });
    return response.data;
  } catch (error) {
    console.error('Error getting bans:', error);
    throw error;
  }
}; 