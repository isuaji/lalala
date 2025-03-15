<template>
  <div class="user-page">
    <div class="content">
      <h1 class="title">USF - Больше чем свалка</h1>
      
      <div class="user-info">
        <div class="avatar-container">
          <img v-if="userInfo.avatar" :src="userInfo.avatar" alt="Avatar" class="user-avatar">
          <div v-else class="avatar-placeholder">{{ getInitials(userInfo.name) }}</div>
        </div>

        <div class="welcome-text">
          {{ userInfo.name }}
        </div>

        <div class="user-details">
          <div class="detail-item">
            <span class="value">ID: {{ userInfo.id }}</span>
          </div>
          
          <div class="detail-item">
            <span :class="['status', { 'banned': userInfo.isBanned }]">
              {{ userInfo.isBanned ? 'В бане' : 'Не в бане' }}
            </span>
          </div>
        </div>

        <div class="search-section">
          <h2 class="search-title">Проверить бан пользователя</h2>
          <div class="search-container">
            <input 
              type="number" 
              v-model="searchUserId" 
              placeholder="Введите ID пользователя"
              class="search-input"
              @keyup.enter="searchBan"
            >
            <button @click="searchBan" class="search-button" :disabled="!searchUserId">
              Поиск
            </button>
          </div>

          <!-- Результаты поиска -->
          <div v-if="searchResult" class="search-results">
            <div v-if="searchResult.is_banned" class="ban-info">
              <div class="ban-header">
                <span class="ban-status">Пользователь заблокирован</span>
                <span class="ban-date">{{ formatDate(searchResult.ban_date) }}</span>
              </div>
              
              <div class="ban-details">
                <div class="detail-row">
                  <span class="label">Админ:</span>
                  <a :href="'https://t.me/' + searchResult.admin.username" 
                     target="_blank" 
                     class="admin-link">
                    @{{ searchResult.admin.username }}
                  </a>
                </div>
                
                <div class="detail-row">
                  <span class="label">Причина:</span>
                  <span class="value">{{ searchResult.reason }}</span>
                </div>
                
                <div class="detail-row">
                  <span class="label">Доказательства:</span>
                  <span class="value">{{ searchResult.proofs }}</span>
                </div>

                <div v-if="searchResult.images && searchResult.images.length > 0" class="images-grid">
                  <img 
                    v-for="(image, index) in searchResult.images" 
                    :key="index"
                    :src="'data:image/jpeg;base64,' + image"
                    @click="openImage(image)"
                    class="ban-image"
                    alt="Доказательство"
                  >
                </div>
              </div>
            </div>
            <div v-else class="no-ban-info">
              Пользователь не заблокирован
            </div>
          </div>
        </div>
      </div>
    </div>

    <footer>
      <div class="footer-content">
        <a href="https://t.me/helloworld22213" target="_blank" class="contact-link">
          @helloworld22213
        </a>
      </div>
    </footer>

    <!-- Модальное окно для просмотра изображений -->
    <div v-if="selectedImage" class="modal" @click="selectedImage = null">
      <img :src="'data:image/jpeg;base64,' + selectedImage" class="modal-image" alt="Увеличенное изображение">
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const userInfo = ref({
  id: null,
  name: '',
  avatar: null,
  isBanned: false
});

const searchUserId = ref('');
const searchResult = ref(null);
const selectedImage = ref(null);

const getInitials = (name) => {
  if (!name) return '?';
  return name.split(' ').map(n => n[0]).join('').toUpperCase();
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

const searchBan = async () => {
  if (!searchUserId.value) return;
  
  try {
    const response = await axios.get(`https://usfbase.ru/USFAPI/public/ban/${searchUserId.value}`);
    searchResult.value = response.data;
  } catch (error) {
    console.error('Ошибка при поиске бана:', error);
    searchResult.value = { is_banned: false };
  }
};

const openImage = (image) => {
  selectedImage.value = image;
};

onMounted(async () => {
  try {
    if (!window.Telegram?.WebApp) return;

    const webApp = window.Telegram.WebApp;
    const user = webApp.initDataUnsafe?.user;
    
    if (!user) return;

    const adminCheckResponse = await axios.get(`https://usfbase.ru/USFAPI/check_admin/${user.id}`);
    if (adminCheckResponse.data.is_admin) {
      window.location.href = '/admin';
      return;
    }

    const banResponse = await axios.get(`https://usfbase.ru/USFAPI/check_ban/${user.id}`);
    
    userInfo.value = {
      id: user.id,
      name: user.first_name,
      avatar: user.photo_url,
      isBanned: banResponse.data.is_banned
    };

    webApp.expand();
    webApp.ready();
  } catch (error) {
    console.error('Ошибка при инициализации:', error);
  }
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

.user-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0F111A;
  color: #FFFFFF;
  font-family: 'JetBrains Mono', monospace;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}

.title {
  font-size: 24px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 40px;
  color: #FFFFFF;
  letter-spacing: -0.5px;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  width: 100%;
  max-width: 320px;
}

.avatar-container {
  width: 120px;
  height: 120px;
  border-radius: 60px;
  overflow: hidden;
  background: #1A1B26;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.user-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 36px;
  font-weight: 700;
  color: #FFFFFF;
}

.welcome-text {
  font-size: 20px;
  font-weight: 700;
  color: #FFFFFF;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.detail-item {
  padding: 12px;
  background: #1A1B26;
  border-radius: 8px;
  text-align: center;
}

.value {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.status {
  font-size: 14px;
  font-weight: 700;
  color: #4CAF50;
}

.status.banned {
  color: #F44336;
}

/* Поисковая секция */
.search-section {
  width: 100%;
  margin-top: 30px;
  padding: 16px;
  background: #1A1B26;
  border-radius: 12px;
}

.search-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
  text-align: center;
}

.search-container {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: 10px 12px;
  background: #2A2C3B;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #FFFFFF;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #3B82F6;
}

.search-button {
  padding: 10px 16px;
  background: #2563eb;
  border: none;
  border-radius: 8px;
  color: #FFFFFF;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 80px;
  flex-shrink: 0;
}

.search-button:hover {
  background: #3b82f6;
  transform: translateY(-1px);
}

.search-button:disabled {
  background: #374151;
  cursor: not-allowed;
  transform: none;
}

/* Результаты поиска */
.search-results {
  margin-top: 20px;
}

.ban-info {
  background: #2A2C3B;
  border-radius: 8px;
  padding: 16px;
}

.ban-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.ban-status {
  color: #F44336;
  font-weight: 700;
}

.ban-date {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.ban-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-row .label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.detail-row .value {
  color: #FFFFFF;
  font-size: 14px;
}

.admin-link {
  color: #3B82F6;
  text-decoration: none;
  transition: color 0.2s ease;
}

.admin-link:hover {
  color: #60A5FA;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.ban-image {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.ban-image:hover {
  transform: scale(1.05);
}

.no-ban-info {
  text-align: center;
  color: #4CAF50;
  font-weight: 700;
  padding: 16px;
}

/* Модальное окно */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  cursor: pointer;
}

.modal-image {
  max-width: 90%;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 8px;
}

footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-content {
  text-align: center;
}

.contact-link {
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s ease;
}

.contact-link:hover {
  color: #FFFFFF;
}

/* Анимации */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.search-results {
  animation: fadeIn 0.3s ease;
}

@media (max-width: 640px) {
  .search-container {
    flex-direction: column;
  }

  .search-input,
  .search-button {
    width: 100%;
  }

  .search-section {
    padding: 12px;
  }

  .ban-details {
    padding: 12px;
  }

  .images-grid {
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  }
}
</style>
