<template>
  <div class="ban-list-container">
    <div class="search-bar">
      <input 
        type="text" 
        v-model="searchQuery"
        placeholder="Поиск по ID пользователя"
        @input="filterBans"
      >
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <span>Загрузка списка банов...</span>
    </div>

    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-else-if="filteredBans.length === 0" class="empty-state">
      <span>{{ searchQuery ? 'Ничего не найдено' : 'Список банов пуст' }}</span>
    </div>

    <div v-else class="bans-grid">
      <div v-for="ban in filteredBans" :key="ban.id" class="ban-item">
        <div class="ban-header">
          <span class="user-id">ID: {{ ban.user_id }}</span>
          <span class="ban-date">{{ formatDate(ban.ban_date) }}</span>
        </div>
        <div class="ban-content">
          <div class="ban-reason">
            <strong>Причина:</strong> {{ ban.reason }}
          </div>
          <div class="ban-proof">
            <strong>Доказательства:</strong> {{ ban.proofs }}
          </div>
          <div v-if="ban.images && ban.images.length > 0" class="ban-images">
            <div 
              v-for="(image, index) in ban.images" 
              :key="index" 
              class="image-container"
              @click="openImage(image)"
            >
              <img 
                :src="image" 
                :alt="`Доказательство ${index + 1}`" 
                class="ban-image"
                @error="$event.target.style.display = 'none'"
              >
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно для просмотра изображений -->
    <div v-if="selectedImage" class="image-modal" @click="selectedImage = null">
      <img :src="selectedImage" alt="Увеличенное изображение" class="modal-image">
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const bans = ref([]);
const loading = ref(true);
const error = ref(null);
const searchQuery = ref('');
const selectedImage = ref(null);

const filteredBans = computed(() => {
  if (!searchQuery.value) return bans.value;
  const query = searchQuery.value.toLowerCase();
  return bans.value.filter(ban => 
    ban.user_id.toString().includes(query)
  );
});

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const openImage = (imageUrl) => {
  selectedImage.value = imageUrl;
};

onMounted(async () => {
  if (window.Telegram?.WebApp) {
    const webApp = window.Telegram.WebApp;
    webApp.BackButton.onClick(() => {
      if (selectedImage.value) {
        selectedImage.value = null;
        return;
      }
      router.back();
    });
    webApp.BackButton.show();
    webApp.ready();
  }
  await fetchBans();
});

const fetchBans = async () => {
  try {
    loading.value = true;
    const response = await axios.get('https://usfbase.ru/USFAPI/bans', {
      headers: {
        'Authorization': window.Telegram.WebApp.initData
      }
    });
    bans.value = response.data.map(ban => ({
      ...ban,
      images: ban.images?.map(img => {
        if (img.startsWith('http')) {
          return img;
        }
        return `data:image/jpeg;base64,${img}`;
      }) || []
    }));
  } catch (e) {
    console.error('Error fetching bans:', e);
    error.value = e.response?.data?.detail || 'Ошибка при получении списка банов';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.ban-list-container {
  padding: 16px;
  min-height: 100vh;
  background: #0F111A;
  color: #FFFFFF;
}

.search-bar {
  margin-bottom: 16px;
}

.search-bar input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #FFFFFF;
  font-size: 14px;
  transition: all 0.3s ease;
}

.search-bar input:focus {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.2);
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.bans-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ban-item {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.ban-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.ban-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.user-id {
  font-weight: 600;
  color: #3B82F6;
}

.ban-date {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.ban-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ban-reason, .ban-proof {
  font-size: 14px;
  line-height: 1.5;
}

.ban-images {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.image-container {
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.ban-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

.image-container:hover {
  transform: scale(1.05);
}

.image-modal {
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
  padding: 20px;
}

.modal-image {
  max-width: 100%;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 8px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 16px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(59, 130, 246, 0.1);
  border-radius: 50%;
  border-top-color: #3B82F6;
  animation: spin 1s linear infinite;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.6);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.error-message {
  padding: 20px;
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(185, 28, 28, 0.1) 100%);
  border: 1px solid rgba(220, 38, 38, 0.2);
  color: #ef4444;
  border-radius: 16px;
  text-align: center;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 640px) {
  .ban-list-container {
    padding: 12px;
  }
  
  .ban-item {
    padding: 16px;
  }
  
  .ban-images {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
}
</style> 