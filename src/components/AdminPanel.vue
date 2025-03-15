<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const loading = ref(true);
const error = ref(null);
const isAdmin = ref(false);
const hasStatsAccess = ref(false);

const adminInfo = ref({
  id: null,
  name: '',
  avatar: null,
  points: 0
});

onMounted(async () => {
  try {
    if (!window.Telegram?.WebApp) {
      router.push('/');
      return;
    }

    const webApp = window.Telegram.WebApp;
    const userId = webApp.initDataUnsafe?.user?.id;
    
    if (!userId) {
      router.push('/');
      return;
    }

    // Получаем аватарку из WebApp API
    adminInfo.value = {
      id: userId,
      name: webApp.initDataUnsafe?.user?.first_name || 'Admin',
      avatar: webApp.initDataUnsafe?.user?.photo_url, // Используем аватарку из WebApp
      points: 0
    };

    const headers = {
      'Authorization': webApp.initData
    };

    // Выполняем все запросы параллельно
    const [checkResponse, adminResponse, currentAdminResponse] = await Promise.all([
      axios.get(`https://usfbase.ru/USFAPI/check_admin/${userId}`, { headers }),
      axios.get(`https://usfbase.ru/USFAPI/admin/${userId}`, { headers }),
      axios.get('https://usfbase.ru/USFAPI/current-admin', { headers })
    ]);

    if (!checkResponse.data.is_admin || currentAdminResponse.data.points === 0) {
      router.push('/');
      return;
    }

    adminInfo.value = {
      id: userId,
      name: adminResponse.data.full_name || webApp.initDataUnsafe?.user?.first_name || 'Admin',
      avatar: adminResponse.data.avatar,
      points: currentAdminResponse.data.points
    };

    webApp.expand();
    webApp.ready();
    loading.value = false;
    isAdmin.value = true;
    hasStatsAccess.value = currentAdminResponse.data.points >= 70;
  } catch (error) {
    console.error('Ошибка при инициализации:', error);
    router.push('/');
  }
});

const navigateToBan = () => {
  router.push('/admin/ban');
};

const navigateToMute = () => {
  router.push('/admin/mute');
};

const handleClose = () => {
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.close();
  } else {
    router.push('/');
  }
};

const adminActions = [
  {
    id: 'ban',
    title: 'Бан',
    description: 'Заблокировать пользователя',
    icon: '⛔'
  },
  {
    id: 'mute',
    title: 'Мут',
    description: 'Временное ограничение',
    icon: '🎤'
  },
  {
    id: 'unban',
    title: 'Разбан',
    description: 'Разблокировать пользователя',
    icon: '✅'
  },
  {
    id: 'banlist',
    title: 'Список банов',
    description: 'Просмотр заблокированных',
    icon: '📋'
  },
  {
    id: 'warnings',
    title: 'Предупреждения',
    description: 'Управление варнами',
    icon: '⚠️'
  },
  {
    id: 'stats',
    title: 'Статистика',
    description: 'Анализ действий',
    icon: '📊'
  }
];

const handleAction = (actionId) => {
  console.log('Выбрано действие:', actionId);
  if (actionId === 'ban') {
    navigateToBan();
  } else if (actionId === 'mute') {
    navigateToMute();
  } else if (actionId === 'unban') {
    router.push({ name: 'unban' });
  } else if (actionId === 'warnings') {
    router.push({ name: 'warn' });
  } else if (actionId === 'banlist') {
    router.push('/admin/banlist');
  } else if (actionId === 'back') {
    router.back();
  }
};

const handleBanClick = () => {
  navigateToBan();
};

const handleMuteClick = () => {
  navigateToMute();
};

const handleBanListClick = () => {
  router.push('/admin/banlist');
};
const handleAdminListClick = () => {
  router.push('/admin/admins');
};

const goToStats = () => {
  router.push('/admin/logs');
};

const addAdmin = async (newAdminId, newAdminPoints) => {
  try {
    const formData = new FormData();
    formData.append('user_id', newAdminId);
    formData.append('points', newAdminPoints);

    const response = await axios.post('https://usfbase.ru/USFAPI/admin/add', 
      formData,
      {
        headers: {
          'Authorization': window.Telegram.WebApp.initData
        }
      }
    );
    
    if (response.data.message) {
      // Обновить список админов
      await fetchAdmins();
      return true;
    }
  } catch (error) {
    console.error('Ошибка при добавлении админа:', error);
    throw error;
  }
};

const getRankLetter = (points) => {
  if (points >= 90) return 'S'
  if (points >= 70) return 'A+'
  if (points >= 50) return 'A'
  if (points >= 30) return 'B'
  if (points >= 15) return 'C'
  return 'D'
};

const getRankClass = (points) => {
  if (points >= 90) return 'rank-s'
  if (points >= 70) return 'rank-aplus'
  if (points >= 50) return 'rank-a'
  if (points >= 30) return 'rank-b'
  if (points >= 15) return 'rank-c'
  return 'rank-d'
};

const handleAvatarError = (e) => {
  e.target.style.display = 'none';
  e.target.parentElement.innerHTML = `<div class="avatar-placeholder">${adminInfo.value.name[0]}</div>`;
};
</script>

<template>
  <div class="admin-container">
    <h1>Панель администратора</h1>
    
    <div class="admin-profile">
      <div class="admin-avatar">
        <img v-if="adminInfo.avatar" 
             :src="adminInfo.avatar + '?t=' + Date.now()" 
             :alt="adminInfo.name"
             @error="handleAvatarError"
        >
        <div v-else class="avatar-placeholder">{{ adminInfo.name[0] }}</div>
      </div>
      <div class="admin-details">
        <div class="admin-name">{{ adminInfo.name }}</div>
        <div class="admin-id">ID: {{ adminInfo.id }}</div>
        <div class="admin-rank" :class="getRankClass(adminInfo.points)">
          Ранг: {{ getRankLetter(adminInfo.points) }}
        </div>
      </div>
    </div>

    <div class="actions-grid">
      <button 
        v-for="action in adminActions" 
        :key="action.id"
        class="action-card"
        @click="handleAction(action.id)"
      >
        <div class="action-icon">{{ action.icon }}</div>
        <h3>{{ action.title }}</h3>
        <p>{{ action.description }}</p>
      </button>
    </div>

    <button class="admin-list-button" @click="handleAdminListClick">
      <span class="button-icon">👥</span>
      <div class="button-text">
        <h3>Список администрации</h3>
        <p>Управление администраторами</p>
      </div>
    </button>

    <button 
      @click="goToStats" 
      class="stats-button"
      :disabled="!hasStatsAccess"
    >
      <span class="button-icon">📊</span>
      <div class="button-text">
        <h3>Логи</h3>
        <p>Анализ активности администрации</p>
      </div>
      <span v-if="!hasStatsAccess" class="rank-required">Требуется ранг A+</span>
    </button>
  </div>
</template>

<style scoped>
.admin-container {
  min-height: 100vh;
  background: #0F111A;
  color: #FFFFFF;
  padding: 20px;
  box-sizing: border-box;
}

h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.admin-profile {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.admin-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.admin-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  font-weight: 600;
}

.admin-details {
  flex: 1;
}

.admin-name {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}

.admin-id {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 4px;
}

.admin-rank {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
}

.rank-s { background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%); color: #000; }
.rank-aplus { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
.rank-a { background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%); }
.rank-b { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
.rank-c { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
.rank-d { background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); }

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.action-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.action-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.action-card h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.action-card p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  text-align: center;
}

.admin-list-button, .stats-button {
  width: 100%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.admin-list-button:hover, .stats-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.button-icon {
  font-size: 24px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.button-text {
  flex: 1;
}

.button-text h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px;
}

.button-text p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.stats-button {
  position: relative;
}

.stats-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.rank-required {
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  color: #ef4444;
  white-space: nowrap;
}

@media (max-width: 640px) {
  .admin-container {
    padding: 16px;
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .action-card {
    padding: 16px;
  }
}
</style>
