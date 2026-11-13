<script setup>
import { auth } from '@/stores/auth'
</script>
<template>
  <div class="page-heading">
    <div>
      <span class="eyebrow">MY ACCOUNT</span>
      <h1>个人中心</h1>
      <p>查看当前账号信息。</p>
    </div>
  </div>
  <section class="profile-panel" v-if="auth.user">
    <span class="avatar large">{{ auth.user.display_name.slice(0, 1) }}</span>
    <h2>{{ auth.user.display_name }}</h2>
    <dl>
      <dt>用户名</dt>
      <dd>{{ auth.user.username }}</dd>
      <dt>当前基础权限</dt>
      <dd>{{ auth.user.is_staff ? '管理员 · 可查看与新增物品' : '成员 · 可查看物品' }}</dd>
    </dl>
    <p class="page-note">
      个人资料编辑与修改密码将在后续版本提供。教师、负责人等业务角色尚未划分。
    </p>
  </section>
</template>
