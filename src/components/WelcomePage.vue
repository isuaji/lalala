<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const loading = ref(true);
const error = ref(null);
const checkingStep = ref(0);
const debugInfo = ref('');
const steps = [
  'Проверка прав доступа',
  'Подготовка админ панели'
];

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

onMounted(async () => {
  try {
    if (!window.Telegram?.WebApp) {
      error.value = 'Ошибка: приложение должно быть открыто в Telegram';
      loading.value = false;
      return;
    }

    const webApp = window.Telegram.WebApp;
    const userId = webApp.initDataUnsafe?.user?.id;
    const initData = webApp.initData;

    if (!userId || !initData) {
      error.value = 'Ошибка: не удалось получить данные пользователя';
      loading.value = false;
      return;
    }

    debugInfo.value = `ID пользователя: ${userId}\n`;
    
    try {
      // Проверяем права доступа
      const response = await axios.get(`https://usfbase.ru/USFAPI/check_admin/${userId}`, {
        headers: {
          'Authorization': initData
        }
      });
      
      debugInfo.value += `Ответ API: ${JSON.stringify(response.data)}\n`;
      
      if (!response.data.is_admin) {
        error.value = '⛔️ У вас нет доступа к админ панели';
        if (webApp.showAlert) {
          webApp.showAlert('⛔️ У вас нет доступа к админ панели');
        }
        loading.value = false;
        return;
      }

      // Проверяем текущие очки админа
      const currentAdminResponse = await axios.get('https://usfbase.ru/USFAPI/current-admin', {
        headers: {
          'Authorization': initData
        }
      });

      if (currentAdminResponse.data.points === 0) {
        error.value = '⛔️ Недостаточно прав для доступа к админ панели';
        if (webApp.showAlert) {
          webApp.showAlert('⛔️ Недостаточно прав для доступа к админ панели');
        }
        loading.value = false;
        return;
      }
      
      localStorage.setItem('adminId', userId);
      localStorage.setItem('initData', initData);
      router.push('/admin');
      
      checkingStep.value = 1;
    } catch (e) {
      debugInfo.value += `Ошибка при обработке: ${e}\n`;
      error.value = 'Ошибка при проверке доступа к админ панели';
      loading.value = false;
      return;
    }

    if (webApp.expand) webApp.expand();
    if (webApp.ready) webApp.ready();
  } catch (e) {
    error.value = `Ошибка при проверке доступа: ${e.message}`;
    debugInfo.value += `Полная ошибка: ${e.toString()}\n`;
    loading.value = false;
  }
});
</script>

<template>
  <div class="welcome-container">
    <div v-if="loading" class="loading-container">
      <div class="loading-circle"></div>
      <div class="steps-container">
        <div 
          v-for="(step, index) in steps" 
          :key="index"
          class="step"
          :class="{
            'active': index === checkingStep,
            'completed': index < checkingStep
          }"
        >
          <div class="step-dot"></div>
          <div class="step-text">{{ step }}</div>
        </div>
      </div>
    </div>
    <div v-else-if="error" class="error">
      {{ error }}
      <pre class="debug-info">{{ debugInfo }}</pre>
    </div>
  </div>
</template>

<style scoped>
.welcome-container {
  min-height: 100vh;
  min-height: 100dvh;
  background: #1A1A1A;
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
}

.loading-circle {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top: 3px solid #FFFFFF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.steps-container {
  display: flex;
  gap: 16px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.step-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: #444;
}

.step-text {
  font-size: 16px;
  font-weight: 500;
}

.active {
  background-color: #FFFFFF;
}

.completed {
  background-color: #444;
}

.error {
  font-size: 16px;
  text-align: center;
  color: #F04A4A;
  animation: fadeIn 0.3s ease;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.debug-info {
  margin-top: 20px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  text-align: left;
}
</style>

