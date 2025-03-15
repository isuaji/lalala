<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const unbanForm = ref({
  userId: '',
  reason: ''
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

const resetForm = () => {
  unbanForm.value.userId = '';
  unbanForm.value.reason = '';
  error.value = null;
  success.value = false;
  loading.value = false;
};

const handleSubmit = async () => {
  try {
    loading.value = true;
    error.value = null;

    const formData = new FormData();
    formData.append('user_id', parseInt(unbanForm.value.userId));
    formData.append('reason', unbanForm.value.reason);

    const response = await axios.post('https://usfbase.ru/USFAPI/unban', 
      formData,
      {
        headers: {
          'Authorization': window.Telegram.WebApp.initData
        }
      }
    );

    if (response.data.status === 'success') {
      success.value = response.data.message || 'Пользователь успешно разблокирован';
      resetForm();
    }
  } catch (e) {
    console.error('Error in handleUnban:', e);
    error.value = e.response?.data?.detail || 'Ошибка при разбане пользователя';
  } finally {
    loading.value = false;
  }
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
      <h1 class="form-title">Разблокировка пользователя</h1>
      <p class="form-subtitle">Заполните форму для разблокировки пользователя</p>
    </div>

    <div class="form-container">
      <form class="unban-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>ID пользователя</label>
          <input 
            type="text" 
            v-model="unbanForm.userId"
            placeholder="Например: 123456789"
            required
            @keydown="handleKeyDown"
          >
        </div>

        <div class="form-group">
          <label>Причина разблокировки</label>
          <textarea 
            v-model="unbanForm.reason"
            placeholder="Опишите причину разблокировки"
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

        <button type="submit" class="submit-button unban-button" :disabled="loading">
          <span v-if="loading" class="loading-icon">⏳</span>
          <span v-else class="unban-icon">✅</span>
          {{ loading ? 'Разблокировка...' : 'Разблокировать пользователя' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
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

.unban-form {
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
  color: var(--tg-theme-text-color);
}

input, textarea {
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  color: var(--tg-theme-text-color);
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
  -webkit-tap-highlight-color: transparent;
  transition: all 0.3s ease;
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
  color: var(--tg-theme-hint-color);
}

input:focus, textarea:focus {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.submit-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2);
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
  transition: all 0.3s ease;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 8px rgba(16, 185, 129, 0.3);
}

.submit-button:active {
  transform: translateY(1px);
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
}

.unban-icon {
  font-size: 18px;
}

.error-message {
  color: #F04A4A;
  font-size: 14px;
  text-align: center;
  padding: 8px;
  background: rgba(240, 74, 74, 0.1);
  border-radius: 8px;
}

.success-message {
  color: #4CAF50;
  font-size: 14px;
  text-align: center;
  padding: 8px;
  background: rgba(76, 175, 80, 0.1);
  border-radius: 8px;
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

.submit-button.unban-button {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2);
}

.submit-button.unban-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 8px rgba(16, 185, 129, 0.3);
}
</style>
