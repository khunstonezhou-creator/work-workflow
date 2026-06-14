/**
 * 权限管理脚本
 * 用于检查用户登录状态和权限
 */

const AUTH_CONFIG = {
  storageKey: 'workbench_users',
  currentUserKey: 'workbench_current_user',
  loginPage: 'auth-system.html'
};

// 获取当前用户
function getAuthUser() {
  const data = localStorage.getItem(AUTH_CONFIG.currentUserKey);
  return data ? JSON.parse(data) : null;
}

// 检查是否已登录
function isAuthenticated() {
  return !!getAuthUser();
}

// 获取用户权限
function getUserRole() {
  const user = getAuthUser();
  return user ? user.role : null;
}

// 检查是否有特定权限
function hasPermission(requiredRole) {
  const userRole = getUserRole();
  if (!userRole) return false;

  const hierarchy = { 'admin': 3, 'internal': 2, 'external': 1 };
  return (hierarchy[userRole] || 0) >= (hierarchy[requiredRole] || 0);
}

// 重定向到登录页面
function redirectToLogin() {
  window.location.href = AUTH_CONFIG.loginPage;
}

// 应用权限控制
function applyPermissions() {
  const user = getAuthUser();
  if (!user) {
    redirectToLogin();
    return;
  }

  // 根据权限显示/隐藏元素
  document.querySelectorAll('[data-permission]').forEach(el => {
    const required = el.getAttribute('data-permission');
    if (!hasPermission(required)) {
      el.style.display = 'none';
    }
  });

  // 外部同学只能看到知识库搜索
  if (user.role === 'external') {
    // 隐藏所有看板
    document.querySelectorAll('.nav, .section, .card').forEach(el => {
      if (!el.closest('#kb-section') && !el.closest('.kb-search')) {
        el.style.display = 'none';
      }
    });

    // 只显示知识库部分
    const kbSection = document.getElementById('kb-section');
    if (kbSection) {
      kbSection.style.display = 'block';
    }
  }

  // 显示用户信息
  const userInfoEl = document.getElementById('user-info');
  if (userInfoEl) {
    userInfoEl.innerHTML = `
      <div style="padding: 8px; background: rgba(255,255,255,0.1); border-radius: 6px; font-size: 11px;">
        <div style="margin-bottom: 4px;">👤 ${user.name}</div>
        <div style="color: ${user.role === 'admin' ? '#4caf50' : '#999'};">
          ${getRoleDisplayName(user.role)}
        </div>
        <div style="margin-top: 8px;">
          <a href="#" onclick="logoutUser()" style="color: #ef4444; font-size: 10px;">退出登录</a>
        </div>
      </div>
    `;
  }
}

// 获取权限显示名称
function getRoleDisplayName(role) {
  const names = {
    'admin': '管理员',
    'internal': '小米内部人',
    'external': '外部同学'
  };
  return names[role] || role;
}

// 退出登录
function logoutUser() {
  localStorage.removeItem(AUTH_CONFIG.currentUserKey);
  window.location.href = AUTH_CONFIG.loginPage;
}

// 页面加载时检查权限
document.addEventListener('DOMContentLoaded', function() {
  // 如果当前页面不是登录页面
  if (!window.location.pathname.includes('auth-system')) {
    if (!isAuthenticated()) {
      redirectToLogin();
      return;
    }
    applyPermissions();
  }
});

// 导出函数供外部使用
window.authSystem = {
  getUser: getAuthUser,
  isAuthenticated,
  getRole: getUserRole,
  hasPermission,
  logout: logoutUser
};
