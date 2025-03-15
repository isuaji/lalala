<template>
  <div class="user-info-container">
    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      Загрузка...
    </div>
    
    <div v-else-if="error" class="error">
      <div class="error-icon">❌</div>
      <div class="error-message">{{ error }}</div>
      <button class="retry-button" @click="loadBanInfo">
        Попробовать снова
      </button>
    </div>
    
    <div v-else-if="banInfo" class="ban-info">
      <div class="ban-header">
        <div class="ban-icon">🚫</div>
        <h2>Информация о блокировке</h2>
      </div>
      
      <div class="info-card">
        <div class="info-group">
          <div class="info-label">
            <span class="icon">👤</span>
            ID пользователя
          </div>
          <div class="info-value user-id">
            <span class="copy-id" @click="copyToClipboard(banInfo.user_id)">
              {{ banInfo.user_id }}
              <span class="copy-icon">📋</span>
            </span>
          </div>
        </div>
        
        <div class="info-group">
          <div class="info-label">
            <span class="icon">📅</span>
            Дата блокировки
          </div>
          <div class="info-value">{{ banInfo.ban_date }}</div>
        </div>
        
        <div class="info-group">
          <div class="info-label">
            <span class="icon">📝</span>
            Причина
          </div>
          <div class="info-value reason">{{ banInfo.reason }}</div>
        </div>
        
        <div class="info-group">
          <div class="info-label">
            <span class="icon">🔍</span>
            Доказательства
          </div>
          <div class="info-value proofs">{{ banInfo.proofs }}</div>
        </div>
      </div>
      
      <div v-if="banInfo.images && banInfo.images.length > 0" class="images-section">
        <div class="images-header">
          <span class="icon">📸</span>
          Скриншоты
        </div>
        <div class="images-grid">
          <div 
            v-for="(image, index) in banInfo.images" 
            :key="index"
            class="image-container"
            @click="showFullImage(image)"
          >
            <img :src="'data:image/jpeg;base64,' + image" alt="Доказательство">
            <div class="image-overlay">
              <span class="view-icon">🔍</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const loading = ref(true);
const error = ref(null);
const banInfo = ref(null);

const loadBanInfo = async () => {
  try {
    loading.value = true;
    error.value = null;
    
    const apiUrl = 'https://usfbase.ru/USFAPI/user_info';
    
  } catch (e) {
    console.error('Error loading ban info:', e);
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};

const showFullImage = (imageBase64) => {
  const newWindow = window.open();
  newWindow.document.write(`
    <img src="data:image/jpeg;base64,${imageBase64}" 
         style="max-width: 100%; height: auto;">
  `);
};

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
  } catch (err) {
    console.error('Failed to copy:', err);
  }
};

onMounted(() => {
  if (window.Telegram?.WebApp) {
    const webApp = window.Telegram.WebApp;
    webApp.expand();
    webApp.ready();
  }
  loadBanInfo();
});
</script>

<style scoped>
.user-info-container {
  min-height: 100vh;
  background: #1A1A1A;
  color: #FFFFFF;
  padding: 16px;
  padding-top: calc(16px + env(safe-area-inset-top));
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 200px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: #FFFFFF;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px;
  text-align: center;
}

.error-icon {
  font-size: 48px;
}

.error-message {
  color: #F04A4A;
  font-size: 16px;
}

.retry-button {
  background: #2C2C2C;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 24px;
  color: #FFFFFF;
  font-size: 14px;
  cursor: pointer;
}

.ban-info {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.ban-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ban-icon {
  font-size: 24px;
}

h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.info-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.icon {
  font-size: 16px;
}

.info-value {
  font-size: 16px;
  line-height: 1.4;
}

.user-id {
  font-family: monospace;
  font-size: 18px;
}

.copy-id {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.copy-icon {
  font-size: 14px;
  opacity: 0.7;
}

.reason, .proofs {
  white-space: pre-wrap;
  word-break: break-word;
}

.images-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.images-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
}

.image-container {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.image-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-container:hover .image-overlay {
  opacity: 1;
}

.view-icon {
  font-size: 24px;
}

@media (hover: none) {
  .image-overlay {
    display: none;
  }
}
</style>
