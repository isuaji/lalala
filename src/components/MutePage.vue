<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const muteForm = ref({
  userId: '',
  reason: '',
  proof: '',
  duration: ''
});

const loading = ref(false);
const error = ref(null);
const success = ref(false);

onMounted(() => {
  if (window.Telegram?.WebApp) {
    const webApp = window.Telegram.WebApp;
    
    webApp.BackButton.onClick(() => {
      router.back();
    });
    webApp.BackButton.show();
    webApp.enableClosingConfirmation();
    webApp.expand();
    webApp.ready();
  }
});

const handleMute = async () => {
  try {
    loading.value = true;
    error.value = '';

    const formData = new FormData();
    const data = {
      user_id: muteForm.value.userId.toString(),
      reason: muteForm.value.reason,
      proofs: muteForm.value.proof,
      duration: muteForm.value.duration
    };

    // Оптимизированная отправка данных
    Object.entries(data).forEach(([key, value]) => {
      formData.append(key, value);
    });

    const response = await axios.post('https://usfbase.ru/USFAPI/mute', 
      formData,
      {
        headers: {
          'Authorization': window.Telegram.WebApp.initData
        },
        timeout: 10000,
        cache: true
      }
    );

    if (response.data.status === 'success') {
      success.value = response.data.message;
      // Используем деструктуризацию для сброса формы
      muteForm.value = {
        userId: '',
        reason: '',
        proof: '',
        duration: ''
      };
    }
  } catch (e) {
    console.error('Error in handleMute:', e);
    error.value = e.response?.data?.detail || 'Ошибка при муте пользователя';
  } finally {
    loading.value = false;
  }
};

// Добавляем валидацию длительности мута
const validateDuration = (duration) => {
  const pattern = /^(\d+)(ч|д)$/;
  return pattern.test(duration);
};

const handleKeyDown = (event) => {
  if (event.key === 'Enter') {
    event.target.blur();
  }
};
</script>

<template>
  <div class="admin-container">
    <div class="form-header">
      <h1 class="form-title">Временное ограничение</h1>
      <p class="form-subtitle">Заполните форму для ограничения пользователя</p>
    </div>

    <div class="form-container">
      <form class="mute-form" @submit.prevent="handleMute">
        <div class="form-group">
          <label>ID пользователя</label>
          <input 
            type="text" 
            v-model="muteForm.userId"
            placeholder="Например: 123456789"
            required
            @keydown="handleKeyDown"
          >
        </div>

        <div class="form-group">
          <label>Длительность мута</label>
          <input 
            type="text" 
            v-model="muteForm.duration"
            placeholder="Например: 24ч или 7д"
            required
            @keydown="handleKeyDown"
          >
        </div>

        <div class="form-group">
          <label>Причина ограничения</label>
          <textarea 
            v-model="muteForm.reason"
            placeholder="Опишите причину ограничения"
            required
            @keydown="handleKeyDown"
          ></textarea>
        </div>

        <div class="form-group">
          <label>Доказательство</label>
          <textarea 
            v-model="muteForm.proof"
            placeholder="Предоставьте доказательства нарушения"
            required
            @keydown="handleKeyDown"
          ></textarea>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="success" class="success-message">
          {{ success }}
        </div>

        <button type="submit" class="submit-button mute-button" :disabled="loading">
          <span v-if="loading" class="loading-icon">⏳</span>
          <span v-else class="mute-icon">🔇</span>
          {{ loading ? 'Применение мута...' : 'Замутить пользователя' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* В начало стилей */
:root {
  height: 100%;
  overflow: hidden;
}

body {
  height: 100%;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

.admin-container {
  height: 100vh;
  height: 100dvh;
  overflow-y: auto;
  background: #0F111A;
  color: #FFFFFF;
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
  padding: 16px;
}

.form-header {
  margin-bottom: 24px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.form-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.form-subtitle {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.form-container {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.mute-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-size: 14px;
  font-weight: 500;
  color: #FFFFFF;
}

input, textarea {
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  color: #FFFFFF;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
  -webkit-tap-highlight-color: transparent;
  transition: all 0.3s ease;
}

input:focus, textarea:focus {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2);
}

textarea {
  min-height: 100px;
  height: 100px;
  resize: none;
  overflow: hidden;
  -webkit-appearance: none;
  scrollbar-width: none;
}

textarea::-webkit-scrollbar {
  display: none;
}

input::placeholder, textarea::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.submit-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border: none;
  border-radius: 8px;
  padding: 12px;
  color: #FFFFFF;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  margin-top: 8px;
  -webkit-tap-highlight-color: transparent;
  width: 100%;
  box-shadow: 0 4px 6px rgba(245, 158, 11, 0.2);
}

.submit-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.submit-button:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow: 0 2px 4px rgba(245, 158, 11, 0.2);
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 8px rgba(245, 158, 11, 0.3);
}

.mute-icon {
  font-size: 18px;
}

.error-message {
  color: #F04A4A;
  font-size: 14px;
  text-align: center;
  padding: 8px;
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(185, 28, 28, 0.1) 100%);
  border-radius: 8px;
  border: 1px solid rgba(220, 38, 38, 0.2);
}

.success-message {
  color: #4CAF50;
  font-size: 14px;
  text-align: center;
  padding: 8px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
  border-radius: 8px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Стили для iOS */
@supports (-webkit-touch-callout: none) {
  .admin-container {
    padding-top: constant(safe-area-inset-top);
    padding-top: env(safe-area-inset-top);
  }
  
  .header {
    padding-top: calc(16px + constant(safe-area-inset-top));
    padding-top: calc(16px + env(safe-area-inset-top));
  }
}
</style>
