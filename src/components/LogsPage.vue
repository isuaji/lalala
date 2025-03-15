<template>
  <div class="logs-page">
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
    
    <div v-else>
      <div class="header">
        <h2 class="title">Логи действий администрации</h2>
        
        <div class="filters">
          <div class="filter-group">
            <select v-model.number="selectedAdmin" class="filter-select">
              <option :value="null">Все администраторы</option>
              <option v-for="admin in admins" 
                      :key="admin.user_id" 
                      :value="admin.user_id">
                @{{ admin.username }}
              </option>
            </select>
            
            <select v-model="selectedActionType" class="filter-select">
              <option value="">Все действия</option>
              <option value="ban">Баны</option>
              <option value="mute">Муты</option>
              <option value="unban">Разбаны</option>
              <option value="warn">Варны</option>
              <option value="admin_add">Добавление админов</option>
              <option value="admin_remove">Удаление админов</option>
              <option value="admin_update">Изменение рангов</option>
            </select>
          </div>
          
          <button @click="fetchLogs" class="refresh-button">
            Обновить
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading-container">
        <div class="spinner"></div>
        <span>Загрузка логов...</span>
      </div>
      
      <div v-else class="logs-container">
        <div v-for="log in logs" :key="log.id" class="log-card">
          <div class="log-header">
            <div class="admin-info">
              <a :href="'https://t.me/' + log.admin.username" 
                 target="_blank" 
                 class="admin-link">
                @{{ log.admin.username }}
              </a>
              <span class="rank-badge" :class="getRankClass(log.admin.points)">
                {{ getRankLetter(log.admin.points) }}
              </span>
              <span v-if="log.admin.points < 90 && log.admin.ip" class="admin-ip">
                IP: {{ log.admin.ip }}
              </span>
            </div>
            <span class="timestamp">{{ formatDate(log.timestamp) }}</span>
          </div>
          
          <div class="log-content">
            <div class="action-type" :class="getActionClass(log.action_type)">
              {{ getActionText(log.action_type) }}
            </div>
            
            <div class="details">
              <span class="target" v-if="log.target_id">
                ID: {{ log.target_id }}
              </span>
              <span class="description">{{ log.details }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();

const logs = ref([]);
const admins = ref([]);
const selectedAdmin = ref(null);
const selectedActionType = ref('');
const error = ref('');
const loading = ref(false);
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

const getActionClass = (type) => {
  const classes = {
    ban: 'action-ban',
    mute: 'action-mute',
    unban: 'action-unban',
    warn: 'action-warn',
    admin_add: 'action-admin-add',
    admin_remove: 'action-admin-remove',
    admin_update: 'action-admin-update'
  };
  return classes[type] || '';
};

const getActionText = (type) => {
  const texts = {
    ban: 'Бан',
    mute: 'Мут',
    unban: 'Разбан',
    warn: 'Предупреждение',
    admin_add: 'Добавление админа',
    admin_remove: 'Удаление админа',
    admin_update: 'Изменение ранга'
  };
  return texts[type] || type;
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const fetchLogs = async () => {
  try {
    error.value = '';
    loading.value = true;
    let url = 'https://usfbase.ru/USFAPI/logs';
    
    const queryParams = {};
    
    if (selectedAdmin.value && !isNaN(selectedAdmin.value)) {
      queryParams.filter_admin = Number(selectedAdmin.value);
    }
    if (selectedActionType.value) {
      queryParams.action_type = selectedActionType.value;
    }
    
    // Выполняем запросы параллельно для обновления и логов, и списка админов
    const [logsResponse, adminsResponse] = await Promise.all([
      axios.get(url, {
        headers: {
          'Authorization': window.Telegram.WebApp.initData
        },
        params: queryParams
      }),
      axios.get('https://usfbase.ru/USFAPI/admins', {
        headers: {
          'Authorization': window.Telegram.WebApp.initData
        }
      })
    ]);

    logs.value = logsResponse.data;
    admins.value = adminsResponse.data;
  } catch (err) {
    console.error('Ошибка при получении данных:', err);
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail;
    } else if (Array.isArray(err.response?.data)) {
      error.value = err.response.data[0]?.msg || 'Ошибка при получении данных';
    } else {
      error.value = 'Ошибка при получении данных';
    }
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  window.Telegram.WebApp.BackButton.show();
  window.Telegram.WebApp.BackButton.onClick(() => {
    router.push('/admin');
  });

  try {
    loading.value = true;
    // Выполняем запросы параллельно
    const [adminsResponse, logsResponse] = await Promise.all([
      axios.get('https://usfbase.ru/USFAPI/admins', {
        headers: { 'Authorization': window.Telegram.WebApp.initData }
      }),
      axios.get('https://usfbase.ru/USFAPI/logs', {
        headers: { 'Authorization': window.Telegram.WebApp.initData }
      })
    ]);

    admins.value = adminsResponse.data;
    logs.value = logsResponse.data;
  } catch (error) {
    console.error('Ошибка при загрузке данных:', error);
    error.value = 'Ошибка при загрузке данных';
  } finally {
    loading.value = false;
  }
});

// Очищаем слушатели при размонтировании компонента
onUnmounted(() => {
  window.Telegram.WebApp.BackButton.hide();
  window.Telegram.WebApp.BackButton.offClick();
});
</script>

<style scoped>
.logs-page {
  width: 100%;
  padding: 20px;
  min-height: 100vh;
  background: #0F111A;
  color: #FFFFFF;
  font-family: 'JetBrains Mono', monospace;
}

.header {
  margin-bottom: 24px;
}

.title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 16px;
  color: #FFFFFF;
}

.filters {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.filter-group {
  display: flex;
  gap: 12px;
  flex: 1;
  min-width: 280px;
}

.filter-select {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: #FFFFFF;
  font-family: 'JetBrains Mono', monospace;
  font-size: 15px;
  flex: 1;
  min-height: 48px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-select:hover {
  background: rgba(255, 255, 255, 0.15);
}

.refresh-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  border-radius: 12px;
  color: #FFFFFF;
  font-family: 'JetBrains Mono', monospace;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 48px;
  min-width: 120px;
}

.refresh-button:hover {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  transform: translateY(-1px);
}

.refresh-button:active {
  transform: scale(0.98);
}

.logs-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: all 0.2s ease;
}

.log-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.admin-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.admin-link {
  color: #3B82F6;
  text-decoration: none;
  font-weight: 600;
}

.admin-link:hover {
  color: #60A5FA;
}

.rank-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 12px;
}

.rank-s { background: #ffd700; color: #000; }
.rank-aplus { background: #ff4d4d; color: #fff; }
.rank-a { background: #ff4d4d; color: #fff; }
.rank-b { background: #3498db; color: #fff; }
.rank-c { background: #2ecc71; color: #fff; }
.rank-d { background: #95a5a6; color: #fff; }

.timestamp {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-left: auto;
  white-space: nowrap;
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-type {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.action-ban { 
  background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
  color: #fff;
}

.action-mute { 
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #000;
}

.action-unban { 
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
}

.action-warn { 
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #fff;
}

.action-admin-add { 
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
}

.action-admin-remove { 
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: #fff;
}

.action-admin-update { 
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  color: #fff;
}

.details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.target {
  font-family: monospace;
  color: rgba(255, 255, 255, 0.6);
}

@media (max-width: 640px) {
  .filters {
    flex-direction: column;
    padding: 12px;
  }
  
  .filter-group {
    flex-direction: column;
    width: 100%;
  }
  
  .filter-select {
    width: 100%;
  }
  
  .refresh-button {
    width: 100%;
  }
  
  .log-card {
    padding: 16px;
  }
}

.error-message {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(185, 28, 28, 0.1) 100%);
  border: 1px solid rgba(220, 38, 38, 0.2);
  color: #ef4444;
  padding: 20px;
  border-radius: 16px;
  margin-bottom: 20px;
  font-size: 15px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 16px;
  color: #fff;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  margin: 20px 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(59, 130, 246, 0.1);
  border-radius: 50%;
  border-top-color: #3b82f6;
  animation: spin 1s ease-in-out infinite;
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.admin-ip {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  margin-left: 8px;
  font-family: monospace;
}
</style>
