<template>
  <div class="admin-list">
    <div class="header">
      <h2 class="title">Список администрации</h2>
      <button v-if="currentAdminRank >= 90" 
              @click="showAddForm = true" 
              class="action-button add"
              :disabled="loading">
        Добавить администратора
      </button>
    </div>
    
    <!-- Форма добавления админа -->
    <div v-if="showAddForm" class="add-form">
      <input type="number"
             v-model="newAdminId"
             placeholder="ID пользователя"
             class="points-input"/>
      <input type="number"
             v-model="newAdminPoints"
             placeholder="Очки (1-100)"
             min="1"
             max="100"
             class="points-input"/>
      <div class="button-group">
        <button @click="addAdmin" class="action-button save">
          Добавить
        </button>
        <button @click="showAddForm = false" class="action-button cancel">
          Отмена
        </button>
      </div>
    </div>

    <!-- Индикатор загрузки -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <span>Загрузка списка администраторов...</span>
    </div>

    <div v-else class="admin-cards">
      <div v-for="admin in admins" :key="admin.user_id" class="admin-card">
        <div class="admin-info">
          <div class="admin-details">
            <div class="username-container">
              <img v-if="admin.avatar" 
                   :src="getAvatarUrl(admin.avatar)"
                   class="avatar"
                   :alt="admin.full_name">
              <span class="username">@{{ admin.username }}</span>
            </div>
            <div class="user-id">ID: {{ admin.user_id }}</div>
            
            <div class="rank-info">
              <div :class="['rank-badge', getRankClass(admin.points)]">
                {{ getRankLetter(admin.points) }}
              </div>
              <div class="rank-details">
                <span class="rank-name">{{ getRankShortName(admin.points) }}</span>
                <span class="points">{{ admin.points }} pts</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="isEditing === admin.user_id" class="edit-form">
          <input type="number" 
                 v-model="selectedPoints" 
                 min="1" 
                 max="100"
                 class="points-input"/>
          <div class="button-group">
            <button @click="saveRank(admin.user_id)" class="action-button save">
              Сохранить
            </button>
            <button @click="cancelEdit" class="action-button cancel">
              Отмена
            </button>
          </div>
        </div>

        <div v-else class="admin-controls" v-if="currentAdminRank >= 90">
          <button @click="startEdit(admin)" class="edit-btn">Изменить</button>
          <button @click="removeAdmin(admin.user_id)" class="delete-btn">Удалить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

export default {
  name: 'AdminList',
  setup() {
    const admins = ref([])
    const isEditing = ref(null)
    const selectedPoints = ref(1)
    const error = ref(null)
    const showAddForm = ref(false)
    const newAdminId = ref('')
    const newAdminPoints = ref(1)
    const currentAdminRank = ref(0)
    const router = useRouter()
    const loading = ref(true)

    const getCurrentAdminRank = async () => {
      try {
        const response = await axios.get('https://usfbase.ru/USFAPI/current-admin', {
          headers: {
            'Authorization': window.Telegram.WebApp.initData
          }
        })
        currentAdminRank.value = response.data.points || 0
      } catch (err) {
        console.error('Ошибка при получении ранга текущего админа:', err)
      }
    }

    const addAdmin = async () => {
      try {
        const formData = new FormData()
        formData.append('user_id', newAdminId.value)
        formData.append('points', newAdminPoints.value)

        await axios.post('https://usfbase.ru/USFAPI/admin/add', formData, {
          headers: {
            'Authorization': window.Telegram.WebApp.initData
          }
        })
        
        showAddForm.value = false
        newAdminId.value = ''
        newAdminPoints.value = 1
        await fetchAdmins()
      } catch (err) {
        error.value = 'Ошибка при добавлении администратора'
        console.error(err)
      }
    }

    const getRankLetter = (points) => {
      if (points >= 90) return 'S'
      if (points >= 70) return 'A+'
      if (points >= 50) return 'A'
      if (points >= 30) return 'B'
      if (points >= 15) return 'C'
      return 'D'
    }

    const getRankClass = (points) => {
      if (points >= 90) return 'rank-s'
      if (points >= 70) return 'rank-aplus'
      if (points >= 50) return 'rank-a'
      if (points >= 30) return 'rank-b'
      if (points >= 15) return 'rank-c'
      return 'rank-d'
    }

    const removeAdmin = async (adminId) => {
      if (!confirm('Вы уверены, что хотите удалить этого администратора?')) return
      
      try {
        await axios.delete(`https://usfbase.ru/USFAPI/admin/${adminId}`, {
          headers: {
            'Authorization': window.Telegram.WebApp.initData
          }
        })
        await fetchAdmins()
      } catch (err) {
        error.value = 'Ошибка при удалении администратора'
        console.error(err)
      }
    }

    const getRankBarColor = (points) => {
      if (points >= 90) return 'bg-gradient-to-b from-yellow-400 to-orange-500'
      if (points >= 70) return 'bg-gradient-to-b from-red-400 to-pink-500'
      if (points >= 50) return 'bg-gradient-to-b from-red-600 to-red-700'
      if (points >= 30) return 'bg-gradient-to-b from-blue-400 to-blue-600'
      if (points >= 15) return 'bg-gradient-to-b from-green-400 to-green-600'
      return 'bg-gradient-to-b from-gray-400 to-gray-600'
    }

    const getRankTextColor = (points) => {
      if (points >= 90) return 'text-yellow-400'
      if (points >= 70) return 'text-red-400'
      if (points >= 50) return 'text-red-500'
      if (points >= 30) return 'text-blue-400'
      if (points >= 15) return 'text-green-400'
      return 'text-gray-400'
    }

    const getRankName = (points) => {
      if (points >= 90) return 'Создатель'
      if (points >= 70) return 'Администратор A+'
      if (points >= 50) return 'Администратор A'
      if (points >= 30) return 'Модератор B'
      if (points >= 15) return 'Помощник C'
      return 'Стажёр D'
    }

    const getRankShortName = (points) => {
      if (points >= 90) return 'Создатель'
      if (points >= 70) return 'Админ A+'
      if (points >= 50) return 'Админ A'
      if (points >= 30) return 'Модератор B'
      if (points >= 15) return 'Помощник C'
      return 'Стажёр D'
    }

    const fetchAdmins = async () => {
      try {
        loading.value = true
        const response = await axios.get('https://usfbase.ru/USFAPI/admins', {
          headers: {
            'Authorization': window.Telegram.WebApp.initData
          }
        })
        admins.value = response.data
      } catch (err) {
        error.value = 'Ошибка при загрузке списка администраторов'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const getAvatarUrl = (fileId) => {
      if (!fileId) return null
      return fileId
    }

    const getInitials = (name) => {
      if (!name) return '?'
      return name.split(' ').map(n => n[0]).join('').toUpperCase()
    }

    const startEdit = (admin) => {
      isEditing.value = admin.user_id
      selectedPoints.value = admin.points
    }

    const cancelEdit = () => {
      isEditing.value = null
      selectedPoints.value = 1
    }

    const saveRank = async (adminId) => {
      try {
        const formData = new FormData()
        formData.append('admin_id', adminId)
        formData.append('points', selectedPoints.value)

        await axios.post('https://usfbase.ru/USFAPI/admin/update', formData, {
          headers: {
            'Authorization': window.Telegram.WebApp.initData
          }
        })

        await fetchAdmins()
        isEditing.value = null
      } catch (err) {
        error.value = 'Ошибка при обновлении ранга'
        console.error(err)
      }
    }

    onMounted(async () => {
      if (window.Telegram?.WebApp) {
        const webApp = window.Telegram.WebApp;
        webApp.expand(); // Расширяем WebApp на весь экран
        webApp.ready(); // Сообщаем WebApp что приложение готово
        
        // Предотвращаем множественные нажатия
        let isNavigating = false;
        webApp.BackButton.show();
        webApp.BackButton.onClick(() => {
          if (isNavigating) return;
          isNavigating = true;
          router.push('/').finally(() => {
            isNavigating = false;
          });
        });
      }
      
      await getCurrentAdminRank();
      await fetchAdmins();
    })

    onUnmounted(() => {
      window.Telegram.WebApp.BackButton.hide();
      window.Telegram.WebApp.BackButton.offClick();
    })

    return {
      admins,
      isEditing,
      selectedPoints,
      error,
      showAddForm,
      newAdminId,
      newAdminPoints,
      currentAdminRank,
      getAvatarUrl,
      getInitials,
      startEdit,
      cancelEdit,
      saveRank,
      getRankLetter,
      getRankClass,
      removeAdmin,
      addAdmin,
      loading,
      getRankName,
      getRankShortName
    }
  }
}
</script>

<style scoped>
.admin-container {
  height: 100vh;
  height: 100dvh;
  overflow-y: auto;
  background: #0F111A;
  color: #FFFFFF;
  padding: 16px;
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

.admin-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.admin-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.admin-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.admin-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.admin-info {
  flex: 1;
}

.admin-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.admin-id {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.admin-rank {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  margin-left: auto;
}

.rank-s { background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%); color: #000; }
.rank-aplus { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
.rank-a { background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%); }
.rank-b { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
.rank-c { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
.rank-d { background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); }

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.error-message {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(185, 28, 28, 0.1) 100%);
  border: 1px solid rgba(220, 38, 38, 0.2);
  color: #ef4444;
  padding: 16px;
  border-radius: 12px;
  text-align: center;
}

.admin-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

/* Добавляем стили для корректного скроллинга */
::-webkit-scrollbar {
  width: 0px;
  background: transparent;
}

/* Обновляем стили контейнера карточки */
.admin-card {
  background: #18191c;
  border-radius: 8px;
  padding: 12px;
  width: 100%;
  border: 1px solid #2f3136;
  position: relative;
  min-height: 90px;
  padding-right: 120px;
  box-sizing: border-box;
}

.admin-info {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.admin-details {
  flex-grow: 1;
}

.username-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  object-fit: cover;
}

.username {
  font-size: 14px;
  color: #fff;
}

.user-id {
  font-size: 12px;
  color: #72767d;
  margin-top: 2px;
}

.rank-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.rank-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: bold;
  font-size: 14px;
  min-width: 32px;
  text-align: center;
}

.rank-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rank-name {
  font-size: 14px;
  color: #fff;
  font-weight: 500;
}

.points {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.admin-controls {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: calc(100% - 24px);
  justify-content: space-between;
}

.delete-btn, .edit-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 90px;
  height: 32px;
}

.delete-btn {
  background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
  color: #fff;
}

.delete-btn:hover {
  background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
  transform: translateY(-1px);
}

.edit-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
}

.edit-btn:hover {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  transform: translateY(-1px);
}

.edit-form {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.points-input {
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #FFFFFF;
  font-size: 14px;
  width: 90px;
  transition: all 0.2s ease;
}

.points-input:focus {
  border-color: #3b82f6;
  outline: none;
  background: rgba(255, 255, 255, 0.15);
}

.button-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-button {
  padding: 8px 16px;
  font-size: 13px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 600;
  width: 100px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-button.save {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: #fff;
}

.action-button.save:hover {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  transform: translateY(-1px);
}

.action-button.cancel {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
  color: #fff;
}

.action-button.cancel:hover {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  transform: translateY(-1px);
}

.action-button.add {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: #fff;
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 15px;
}

.action-button.add:hover {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  transform: translateY(-1px);
}

.add-form {
  background: #1F2937;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: #3b82f6;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Обновляем стили для мобильных устройств */
@media (max-width: 640px) {
  .admin-list {
    padding: 12px;
    padding-top: calc(12px + env(safe-area-inset-top, 12px));
    padding-bottom: calc(12px + env(safe-area-inset-bottom, 12px));
  }
  
  .header {
    margin-bottom: 12px;
  }
  
  .admin-card {
    padding: 10px;
    padding-right: 110px;
  }
}

.action-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  pointer-events: none;
}

.edit-btn:disabled,
.delete-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  pointer-events: none;
}
</style>
