module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'http://85.193.91.137:8000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': ''
        }
      }
    }
  }
} 