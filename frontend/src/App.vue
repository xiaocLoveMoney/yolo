<template>
  <div id="app">
    <nav class="navbar">
      <div class="nav-brand">YOLO训练平台</div>
      <div class="nav-links">
        <router-link to="/">首页</router-link>
        <router-link to="/datasets">数据集</router-link>
        <router-link to="/annotate">标注</router-link>
        <router-link to="/train">训练</router-link>
        <router-link to="/models">模型管理</router-link>
        <router-link to="/infer">推理</router-link>
        <router-link to="/video-infer">视频推理</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.navbar {
  background: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: bold;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background 0.3s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  background: #34495e;
}

.main-content {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}
</style>
