import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// Глобальная обработка ошибок
window.onerror = function(message, source, lineno, colno, error) {
  console.error('Global error:', { message, source, lineno, colno, error });
  return false;
};

const app = createApp(App)
app.use(router)
app.mount('#app')
