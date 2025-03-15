<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const groups = ref([]);
const loading = ref(true);
const error = ref(null);

const newGroupId = ref('');
const showAddModal = ref(false);
const addingGroup = ref(false);
const addError = ref(null);

onMounted(async () => {
  if (window.Telegram?.WebApp) {
    const webApp = window.Telegram.WebApp;
    webApp.BackButton.onClick(() => router.back());
    webApp.BackButton.show();
    webApp.expand();
    webApp.ready();
  }
  
  await fetchGroups();
});

const fetchGroups = async () => {
  try {
    loading.value = true;
    error.value = null;
    
    const response = await axios.get('https://usfbase.ru/USFAPI/groups', {
      headers: {
        'Authorization': window.Telegram.WebApp.initData
      }
    });
    
    groups.value = response.data;
  } catch (e) {
    console.error('Ошибка при получении списка групп:', e);
    error.value = e.response?.data?.detail || 'Ошибка при получении списка групп';
  } finally {
    loading.value = false;
  }
};

const formatMembersCount = (count) => {
  if (count >= 1000000) {
    return (count / 1000000).toFixed(1) + 'M';
  }
  if (count >= 1000) {
    return (count / 1000).toFixed(1) + 'K';
  }
  return count.toString();
};

const openAddModal = () => {
  showAddModal.value = true;
  newGroupId.value = '';
  addError.value = null;
};

const closeAddModal = () => {
  showAddModal.value = false;
  addingGroup.value = false;
  addError.value = null;
};

const addGroup = async () => {
  try {
    addingGroup.value = true;
    addError.value = null;
    
    const groupIdNumber = parseInt(newGroupId.value);
    if (isNaN(groupIdNumber)) {
      throw new Error('ID группы должен быть числом');
    }
    
    const formData = new FormData();
    formData.append('group_id', groupIdNumber);
    
    await axios.post('https://usfbase.ru/USFAPI/groups/add', 
      formData,
      {
        headers: {
          'Authorization': window.Telegram.WebApp.initData
        }
      }
    );
    
    await fetchGroups();
    closeAddModal();
  } catch (e) {
    console.error('Ошибка при добавлении группы:', e);
    addError.value = e.response?.data?.detail || e.message || 'Ошибка при добавлении группы';
  } finally {
    addingGroup.value = false;
  }
};

const removeGroup = async (groupId) => {
  if (!confirm('Вы уверены, что хотите удалить эту группу?')) {
    return;
  }
  
  try {
    error.value = null;
    await axios.delete(`https://usfbase.ru/USFAPI/groups/${groupId}`, {
      headers: {
        'Authorization': window.Telegram.WebApp.initData
      }
    });
    
    await fetchGroups();
  } catch (e) {
    console.error('Ошибка при удалении группы:', e);
    error.value = e.response?.data?.detail || 'Ошибка при удалении группы';
  }
};
</script>

<template>
  <div class="admin-container">
    <div class="header">
      <h1 class="title">Управление группами</h1>
      <p class="subtitle">Список подключенных групп и каналов</p>
      <button class="add-button" @click="openAddModal">
        <span class="icon">+</span>
        Добавить группу
      </button>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <span>Загрузка групп...</span>
    </div>

    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-else class="groups-container">
      <div v-for="group in groups" :key="group.id" class="group-card">
        <div class="group-avatar">
          <img 
            v-if="group.photo" 
            :src="group.photo" 
            :alt="group.title"
            @error="$event.target.style.display='none'"
          >
          <div v-else class="avatar-placeholder">
            {{ group.title[0] }}
          </div>
        </div>

        <div class="group-info">
          <h3 class="group-title">{{ group.title }}</h3>
          <a 
            v-if="group.username" 
            :href="'https://t.me/' + group.username"
            target="_blank" 
            class="group-username"
          >
            @{{ group.username }}
          </a>
          <span v-else class="group-id">ID: {{ group.id }}</span>
        </div>

        <div class="group-stats">
          <div class="members-count">
            <span class="count">{{ formatMembersCount(group.members_count) }}</span>
            <span class="label">участников</span>
          </div>
        </div>

        <div class="group-actions">
          <button class="remove-button" @click="removeGroup(group.id)">
            <span class="icon">🗑</span>
            Удалить
          </button>
        </div>
      </div>
    </div>

    <!-- Модальное окно добавления группы -->
    <div v-if="showAddModal" class="modal-overlay" @click="closeAddModal">
      <div class="modal-content" @click.stop>
        <h2>Добавить группу</h2>
        <div class="modal-form">
          <div class="form-group">
            <label>ID группы</label>
            <input 
              type="text" 
              v-model="newGroupId"
              placeholder="Например: -100123456789"
              @keydown.enter="addGroup"
            >
            <p class="help-text">
              ID можно получить, переслав любое сообщение из группы боту @getmyid_bot
            </p>
          </div>

          <div v-if="addError" class="error-message">
            {{ addError }}
          </div>

          <div class="modal-actions">
            <button class="cancel-button" @click="closeAddModal">Отмена</button>
            <button 
              class="confirm-button" 
              @click="addGroup"
              :disabled="addingGroup"
            >
              <span v-if="addingGroup" class="loading-icon">⏳</span>
              <span v-else>Добавить</span>
            </button>
          </div>
        </div>
      </div>
    </div>
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

.header {
  margin-bottom: 24px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.groups-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.group-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.group-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.group-avatar {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  overflow: hidden;
  flex-shrink: 0;
}

.group-avatar img {
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

.group-info {
  flex: 1;
  min-width: 0;
}

.group-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.group-username {
  color: #3b82f6;
  text-decoration: none;
  font-size: 14px;
}

.group-id {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

.group-stats {
  text-align: right;
  flex-shrink: 0;
}

.members-count {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.count {
  font-size: 18px;
  font-weight: 600;
  color: #10b981;
}

.label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 16px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(59, 130, 246, 0.1);
  border-radius: 50%;
  border-top-color: #3b82f6;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(185, 28, 28, 0.1) 100%);
  border: 1px solid rgba(220, 38, 38, 0.2);
  color: #ef4444;
  padding: 16px;
  border-radius: 12px;
  text-align: center;
}

.add-button {
  margin-top: 16px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 12px;
  color: #FFFFFF;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.add-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2);
}

.add-button .icon {
  font-size: 18px;
}

.group-actions {
  display: flex;
  gap: 8px;
}

.remove-button {
  padding: 8px 16px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border: none;
  border-radius: 8px;
  color: #FFFFFF;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.remove-button .icon {
  font-size: 14px;
}

.remove-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #1F2937;
  border-radius: 16px;
  padding: 24px;
  width: 90%;
  max-width: 480px;
}

.modal-content h2 {
  margin: 0 0 16px;
  font-size: 20px;
  color: #FFFFFF;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.help-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 16px;
}

.cancel-button {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #FFFFFF;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.confirm-button {
  padding: 8px 16px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 8px;
  color: #FFFFFF;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.confirm-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@media (max-width: 640px) {
  .admin-container {
    padding: 16px;
  }
  
  .group-card {
    padding: 12px;
  }
  
  .group-avatar {
    width: 48px;
    height: 48px;
  }
}

.form-group input {
  width: 100%;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #FFFFFF;
  font-size: 14px;
  transition: all 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #FFFFFF;
  font-size: 14px;
  font-weight: 500;
}
</style>
