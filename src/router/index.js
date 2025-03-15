import { createRouter, createWebHistory } from 'vue-router';
import WelcomePage from '../components/WelcomePage.vue';
import AdminPanel from '../components/AdminPanel.vue';
import BanPage from '../components/BanPage.vue';
import MutePage from '../components/MutePage.vue';
import UnBanPage from '../components/UnBanPage.vue';
import WarnPage from '../components/WarnPage.vue';
import BanList from '../components/BanList.vue';
import AdminList from '../components/AdminList.vue';
import LogsPage from '../components/LogsPage.vue';

const routes = [
  {
    path: '/',
    name: 'welcome',
    component: WelcomePage
  },
  {
    path: '/admin',
    name: 'admin',
    component: AdminPanel,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/ban',
    name: 'ban',
    component: BanPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/mute',
    name: 'mute',
    component: MutePage,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/unban',
    name: 'unban',
    component: UnBanPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/warn',
    name: 'warn',
    component: WarnPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/banlist',
    name: 'banlist',
    component: BanList,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/admins',
    name: 'admins',
    component: AdminList,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/logs',
    name: 'logs',
    component: LogsPage,
    meta: { requiresAuth: true, requiresRank: 70 }
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

// Навигационный guard для проверки доступа
router.beforeEach(async (to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // Проверяем наличие Telegram WebApp
    if (!window.Telegram?.WebApp) {
      next('/')
      return
    }

    const webApp = window.Telegram.WebApp
    const userId = webApp.initDataUnsafe?.user?.id
    const initData = webApp.initData

    if (!userId || !initData) {
      next('/')
      return
    }

    try {
      // Проверяем права доступа
      const response = await fetch(`https://usfbase.ru/USFAPI/check_admin/${userId}`, {
        headers: {
          'Authorization': initData
        }
      })
      
      const data = await response.json()
      
      if (!data.is_admin) {
        next('/')
        return
      }

      // Проверяем требования к рангу
      if (to.meta.requiresRank && data.points < to.meta.requiresRank) {
        next('/admin') // Перенаправляем на админ панель если ранг недостаточный
        return
      }

      next()
    } catch (error) {
      console.error('Ошибка при проверке прав:', error)
      next('/')
    }
  } else {
    next()
  }
})

export default router; 