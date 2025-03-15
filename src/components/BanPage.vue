<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const banForm = ref({
  userId: '',
  reason: '',
  proof: ''
});

const selectedImages = ref([]);
const adminId = ref(null);
const loading = ref(false);
const error = ref(null);
const success = ref(false);

onMounted(() => {
  if (window.Telegram?.WebApp) {
    const webApp = window.Telegram.WebApp;
    adminId.value = webApp.initDataUnsafe?.user?.id;
    
    let isNavigating = false
    webApp.BackButton.onClick(() => {
      if (isNavigating) return
      isNavigating = true
      router.back().finally(() => {
        isNavigating = false
      })
    });
    webApp.BackButton.show();
    webApp.enableClosingConfirmation();
    webApp.expand();
    webApp.ready();
  }
});

const handleImageSelect = (event) => {
  const files = Array.from(event.target.files);
  
  files.forEach(file => {
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        selectedImages.value.push({
          file: file,
          preview: e.target.result
        });
      };
      reader.readAsDataURL(file);
    }
  });
};

const removeImage = (index) => {
  selectedImages.value.splice(index, 1);
};

const resetForm = () => {
  banForm.value.userId = '';
  banForm.value.reason = '';
  banForm.value.proof = '';
  selectedImages.value = [];
  error.value = null;
  success.value = false;
  loading.value = false;
};

const handleBan = async () => {
  try {
    loading.value = true;
    error.value = '';

    const formData = new FormData();
    formData.append('user_id', banForm.value.userId.toString());
    formData.append('reason', banForm.value.reason);
    formData.append('proofs', banForm.value.proof);
    
    if (selectedImages.value) {
      for (const image of selectedImages.value) {
        formData.append('images', image.file);
      }
    }

    await axios.post('https://usfbase.ru/USFAPI/ban', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': window.Telegram.WebApp.initData
      }
    });
    
    success.value = true;
    resetForm();
  } catch (e) {
    console.error('Error in handleBan:', e);
    error.value = e.response?.data?.detail || 'Ошибка при бане пользователя';
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
      <h1 class="form-title">Блокировка пользователя</h1>
      <p class="form-subtitle">Заполните форму для блокировки пользователя</p>
    </div>

    <div class="form-container">
      <form @submit.prevent="handleBan">
        <div class="form-group">
          <label>ID пользователя</label>
          <input 
            type="text" 
            v-model="banForm.userId"
            placeholder="Например: 123456789"
            required
            @keydown="handleKeyDown"
          >
        </div>

        <div class="form-group">
          <label>Причина блокировки</label>
          <textarea 
            v-model="banForm.reason"
            placeholder="Опишите причину блокировки"
            required
            @keydown="handleKeyDown"
          ></textarea>
        </div>

        <div class="form-group">
          <label>Доказательство</label>
          <textarea 
            v-model="banForm.proof"
            placeholder="Предоставьте текстовые доказательства нарушения"
            required
            @keydown="handleKeyDown"
          ></textarea>
        </div>

        <div class="form-group">
          <label>Загрузить скриншоты</label>
          <div class="file-input-container">
            <input 
              type="file" 
              accept="image/*" 
              multiple 
              @change="handleImageSelect"
              class="file-input"
            >
          </div>
          
          <div v-if="selectedImages.length > 0" class="image-previews">
            <div 
              v-for="(image, index) in selectedImages" 
              :key="index" 
              class="image-preview-container"
            >
              <img :src="image.preview" class="image-preview">
              <button 
                type="button" 
                class="remove-image" 
                @click="removeImage(index)"
              >
                ×
              </button>
            </div>
          </div>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="success" class="success-message">
          {{ success }}
        </div>

        <button type="submit" class="submit-button ban-button" :disabled="loading">
          <span v-if="loading" class="loading-icon">⏳</span>
          <span v-else class="action-icon">⛔</span>
          {{ loading ? 'Блокировка...' : 'Заблокировать пользователя' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
:root, body {
  margin: 0;
  padding: 0;
  width: 100%;
  min-height: 100vh;
  background: #1A1A1A;
  color: #FFFFFF;
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
  -webkit-touch-callout: none;
  overscroll-behavior: none;
  overflow: hidden;
}

.admin-container {
  min-height: 100vh;
  min-height: 100dvh;
  background: #0F111A;
  color: #FFFFFF;
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
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

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.9);
}

input, textarea {
  width: 100%;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px 16px;
  color: #FFFFFF;
  font-size: 15px;
  transition: all 0.3s ease;
}

input:focus, textarea:focus {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  outline: none;
}

textarea {
  min-height: 120px;
  resize: vertical;
}

.file-input-container {
  position: relative;
  margin-top: 16px;
}

.file-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.07);
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.file-input:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(59, 130, 246, 0.5);
}

.image-previews {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.image-preview-container {
  position: relative;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.image-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-image {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 14px;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  color: #FFFFFF;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.remove-image:hover {
  background: rgba(220, 38, 38, 0.8);
  transform: scale(1.1);
}

.submit-button {
  width: 100%;
  padding: 14px;
  border-radius: 12px;
  border: none;
  font-size: 16px;
  font-weight: 600;
  color: #FFFFFF;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
}

/* Стили кнопок для разных действий */
.ban-button {
  background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
  box-shadow: 0 4px 6px rgba(220, 38, 38, 0.2);
}

.error-message {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(185, 28, 28, 0.1) 100%);
  border: 1px solid rgba(220, 38, 38, 0.2);
  color: #ef4444;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 20px;
  font-size: 14px;
  text-align: center;
}

.success-message {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: #10b981;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 20px;
  font-size: 14px;
  text-align: center;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 640px) {
  .admin-container {
    padding: 16px;
  }
  
  .form-container {
    padding: 20px;
  }
  
  .image-previews {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
}
</style>
