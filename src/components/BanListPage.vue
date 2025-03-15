<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const bans = ref([]);
const loading = ref(true);
const error = ref(null);
const searchQuery = ref('');
const displayLimit = ref(5);
const searchTimeout = ref(null);
const debugInfo = ref('');

// Отфильтрованные баны
const filteredBans = computed(() => {
  if (!searchQuery.value) return bans.value;
  const query = searchQuery.value.toLowerCase().trim();
  return bans.value.filter(ban => 
    String(ban.user_id).includes(query)
  );
});

// Отображаемые баны с учетом лимита
const displayedBans = computed(() => {
  return filteredBans.value.slice(0, displayLimit.value);
});

// Есть ли еще баны для показа
const hasMoreBans = computed(() => {
  return displayLimit.value < filteredBans.value.length;
});

// Функция для загрузки дополнительных банов
const loadMore = () => {
  displayLimit.value += 5;
};

// Состояние для слайдера
const isSliderOpen = ref(false);
const currentImages = ref([]);
const currentImageIndex = ref(0);

const openSlider = (images, startIndex = 0) => {
  currentImages.value = images;
  currentImageIndex.value = startIndex;
  isSliderOpen.value = true;
};

const closeSlider = () => {
  isSliderOpen.value = false;
  currentImages.value = [];
  currentImageIndex.value = 0;
};

const nextImage = () => {
  if (currentImageIndex.value < currentImages.value.length - 1) {
    currentImageIndex.value++;
  }
};

const prevImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--;
  }
};

const openImage = (imageBase64) => {
  if (window.Telegram?.WebApp) {
    // Открываем изображение в нативном просмотрщике Telegram
    window.Telegram.WebApp.openLink(`data:image/jpeg;base64,${imageBase64}`);
  }
};

// Функция для загрузки банов
const loadBans = async (searchId = '') => {
  try {
    loading.value = true;
    error.value = null;
    debugInfo.value = '';
    
    const webApp = window.Telegram?.WebApp;
    
    const apiUrl = 'https://usfbase.ru/USFAPI/bans';
    debugInfo.value += `Отправляем запрос на: ${apiUrl}${searchId ? `?search_id=${searchId}` : ''}\n`;
    
    const response = await axios.get(`${apiUrl}${searchId ? `?search_id=${searchId}` : ''}`, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': JSON.stringify({ 
          id: webApp?.initDataUnsafe?.user?.id || '7980053081'
        })
      },
      withCredentials: false
    });

    debugInfo.value += `Статус ответа: ${response.status}\n`;
    debugInfo.value += `Заголовки ответа: ${JSON.stringify(response.headers)}\n`;
    debugInfo.value += `Тип данных: ${typeof response.data}\n`;
    debugInfo.value += `Данные: ${JSON.stringify(response.data)}\n`;
    
    // Проверяем, является ли ответ HTML
    if (typeof response.data === 'string' && response.data.includes('<!DOCTYPE html>')) {
      throw new Error('Сервер вернул HTML вместо JSON. Проверьте настройки прокси и CORS.');
    }

    // Проверяем формат данных
    if (!response.data) {
      throw new Error('Нет данных от сервера');
    }

    // Если данные пришли не в виде массива, но это объект с данными банов
    const bansArray = Array.isArray(response.data) ? response.data : 
                     (response.data.bans ? response.data.bans : [response.data]);
    
    debugInfo.value += `Обработанные данные: ${JSON.stringify(bansArray, null, 2)}\n`;
    
    bans.value = bansArray.map(ban => ({
      ...ban,
      ban_date: ban.ban_date ? new Date(ban.ban_date).toLocaleString('ru-RU') : 'Дата не указана'
    }));

    debugInfo.value += `Финальный результат: ${JSON.stringify(bans.value, null, 2)}\n`;
  } catch (e) {
    debugInfo.value += `Полная ошибка: ${e.message}\n`;
    debugInfo.value += `Стек ошибки: ${e.stack}\n`;
    error.value = `Ошибка при загрузке списка банов: ${e.message}`;
  } finally {
    loading.value = false;
  }
};

// Обновляем список при возвращении на страницу
const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible') {
    loadBans(searchQuery.value);
  }
};

// Следим за изменениями в поле поиска
watch(searchQuery, (newValue) => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  
  searchTimeout.value = setTimeout(() => {
    loadBans(newValue);
  }, 300);
});

onMounted(() => {
  if (window.Telegram?.WebApp) {
    const webApp = window.Telegram.WebApp;
    webApp.BackButton.show();
    webApp.BackButton.onClick(() => {
      if (isSliderOpen.value) {
        closeSlider();
      } else {
        router.push('/admin');
      }
    });
  }
  
  // Загружаем баны при монтировании
  loadBans();
  
  // Добавляем слушатель изменения видимости страницы
  document.addEventListener('visibilitychange', handleVisibilityChange);
});

onUnmounted(() => {
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.BackButton.hide();
  }
  // Удаляем слушатель при размонтировании
  document.removeEventListener('visibilitychange', handleVisibilityChange);
});
</script>

<template>
  <div class="ban-list-container">
    <h1 class="page-title">Список банов</h1>

    <div v-if="loading" class="loading">
      Загрузка списка банов...
    </div>

    <div v-else-if="error" class="error">
      {{ error }}
      <pre v-if="debugInfo" class="debug-info">{{ debugInfo }}</pre>
    </div>

    <div v-else>
      <!-- Поле поиска -->
      <div class="search-container">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Поиск по ID пользователя..."
          class="search-input"
        >
      </div>

      <pre v-if="debugInfo" class="debug-info">{{ debugInfo }}</pre>

      <div v-if="filteredBans.length === 0" class="empty-state">
        {{ searchQuery ? 'Баны не найдены' : 'Список банов пуст' }}
      </div>

      <div v-else class="bans-list">
        <div v-for="ban in displayedBans" :key="ban.id" class="ban-card">
          <div class="ban-header">
            <div class="user-id">ID: {{ ban.user_id }}</div>
            <div class="ban-date">{{ ban.ban_date }}</div>
          </div>
          
          <div class="ban-content">
            <div class="reason">
              <span class="label">Причина:</span>
              <span class="text">{{ ban.reason }}</span>
            </div>
            
            <div class="proofs">
              <span class="label">Доказательства:</span>
              <span class="text">{{ ban.proofs }}</span>
            </div>

            <div v-if="ban.images?.length" class="screenshots">
              <span class="label">Скриншоты:</span>
              <div class="screenshots-grid">
                <div 
                  v-for="(image, index) in ban.images" 
                  :key="index"
                  class="screenshot-container"
                >
                  <img 
                    :src="'data:image/jpeg;base64,' + image"
                    class="screenshot"
                    @click="openSlider(ban.images, index)"
                  >
                </div>
              </div>
            </div>
          </div>

          <div class="ban-footer">
            <div class="admin-id">Администратор: {{ ban.admin_id }}</div>
          </div>
        </div>

        <!-- Кнопка "Показать ещё" -->
        <button 
          v-if="hasMoreBans"
          @click="loadMore"
          class="load-more-button"
        >
          Показать ещё...
        </button>
      </div>
    </div>

    <!-- Слайдер изображений -->
    <div v-if="isSliderOpen" class="slider-overlay" @click="closeSlider">
      <div class="slider-container" @click.stop>
        <button class="slider-close" @click="closeSlider">×</button>
        
        <div class="slider-content">
          <button 
            v-if="currentImageIndex > 0" 
            class="slider-nav prev" 
            @click="prevImage"
          >
            ‹
          </button>
          
          <img 
            :src="'data:image/jpeg;base64,' + currentImages[currentImageIndex]"
            class="slider-image"
          >
          
          <button 
            v-if="currentImageIndex < currentImages.length - 1" 
            class="slider-nav next" 
            @click="nextImage"
          >
            ›
          </button>
        </div>
        
        <div class="slider-counter">
          {{ currentImageIndex + 1 }} / {{ currentImages.length }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ban-list-container {
  min-height: 100vh;
  min-height: 100dvh;
  background: #1A1A1A;
  color: #FFFFFF;
  padding: 16px;
  padding-top: calc(16px + env(safe-area-inset-top, 16px));
  padding-bottom: calc(16px + env(safe-area-inset-bottom, 16px));
}

.back-button {
  background: none;
  border: none;
  color: #FFFFFF;
  font-size: 15px;
  padding: 0;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.back-icon {
  font-size: 18px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: 32px 16px;
  font-size: 16px;
}

.error {
  color: #F04A4A;
}

.bans-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ban-card {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
}

.ban-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.user-id {
  font-weight: 500;
}

.ban-date {
  font-size: 14px;
  opacity: 0.7;
}

.ban-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}

.reason, .proofs {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 14px;
  opacity: 0.7;
}

.text {
  font-size: 15px;
  word-break: break-word;
}

.ban-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 12px;
  font-size: 14px;
  opacity: 0.7;
}

.screenshots {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.screenshots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
}

.screenshot-container {
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.2);
}

.screenshot {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
}

.screenshot:active {
  opacity: 0.8;
}

.slider-overlay {
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
}

.slider-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.slider-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 40px;
  height: 40px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #FFFFFF;
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 1001;
}

.slider-content {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.slider-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  padding: 16px;
}

.slider-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 60px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #FFFFFF;
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.slider-nav.prev {
  left: 16px;
  border-radius: 0 30px 30px 0;
}

.slider-nav.next {
  right: 16px;
  border-radius: 30px 0 0 30px;
}

.slider-counter {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.5);
  color: #FFFFFF;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
}

@supports (-webkit-touch-callout: none) {
  .ban-list-container {
    padding-top: calc(16px + constant(safe-area-inset-top));
    padding-top: calc(16px + env(safe-area-inset-top));
    padding-bottom: calc(16px + constant(safe-area-inset-bottom));
    padding-bottom: calc(16px + env(safe-area-inset-bottom));
  }
}

.search-container {
  margin-bottom: 16px;
}

.search-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #FFFFFF;
  font-size: 15px;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.search-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
}

.load-more-button {
  width: 100%;
  padding: 12px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #FFFFFF;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 16px;
}

.load-more-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.load-more-button:active {
  background: rgba(255, 255, 255, 0.15);
}

.debug-info {
  margin: 16px 0;
  padding: 12px;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 8px;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  color: #fff;
  max-height: 300px;
  overflow-y: auto;
}
</style>
