/**
 * 权限管理脚本
 * 用于检查用户登录状态和权限
 */

const AUTH_CONFIG = {
  storageKey: 'workbench_users',
  currentUserKey: 'workbench_current_user',
  loginPage: 'auth-system.html',
  setupPage: 'setup.html'
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

// 检查系统是否已初始化（是否有管理员）
function isSystemInitialized() {
  const data = localStorage.getItem(AUTH_CONFIG.storageKey);
  if (!data) return false;
  const users = JSON.parse(data);
  return users.approved && users.approved.some(u => u.role === 'admin');
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

// 重定向到设置页面
function redirectToSetup() {
  window.location.href = AUTH_CONFIG.setupPage;
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
    // 隐藏所有非知识库的导航
    document.querySelectorAll('.nav').forEach(el => {
      if (el.id !== 'nav-kb' && !el.textContent.includes('知识库')) {
        el.style.display = 'none';
      }
    });

    // 隐藏非知识库的内容区域
    document.querySelectorAll('.tab').forEach(el => {
      if (el.id !== 't-kb') {
        el.style.display = 'none';
      }
    });
  }

  // 管理员显示管理后台链接
  if (user.role === 'admin') {
    const adminLink = document.getElementById('admin-link');
    if (adminLink) {
      adminLink.style.display = 'inline';
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
  // 如果当前页面是登录页面或设置页面，不做检查
  const currentPage = window.location.pathname.split('/').pop();
  if (currentPage === 'auth-system.html' || currentPage === 'setup.html') {
    return;
  }

  // 检查系统是否已初始化
  if (!isSystemInitialized()) {
    redirectToSetup();
    return;
  }

  // 检查是否已登录
  if (!isAuthenticated()) {
    redirectToLogin();
    return;
  }

  // 应用权限
  applyPermissions();
});

// 导出函数供外部使用
window.authSystem = {
  getUser: getAuthUser,
  isAuthenticated,
  isInitialized: isSystemInitialized,
  getRole: getUserRole,
  hasPermission,
  logout: logoutUser
};
