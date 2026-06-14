/**
 * 管理员账号初始化脚本
 * 首次部署时运行此脚本设置管理员账号
 */

(function() {
  const STORAGE_KEY = 'workbench_users';
  const CURRENT_USER_KEY = 'workbench_current_user';

  // 管理员配置
  const ADMIN_CONFIG = {
    email: 'zhouruiqing1@xiaomi.com',
    name: '周睿卿',
    dept: '摄像机接入',
    role: 'admin'
  };

  // 获取现有用户数据
  function getUsers() {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : { approved: [], pending: [] };
  }

  // 保存用户数据
  function saveUsers(users) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(users));
  }

  // 初始化管理员账号
  function initAdmin() {
    const users = getUsers();

    // 检查管理员是否已存在
    const existingAdmin = users.approved.find(u => u.email === ADMIN_CONFIG.email);
    if (existingAdmin) {
      console.log('✅ 管理员账号已存在:', existingAdmin.email);
      // 确保是管理员权限
      if (existingAdmin.role !== 'admin') {
        existingAdmin.role = 'admin';
        saveUsers(users);
        console.log('✅ 已更新管理员权限');
      }
      return;
    }

    // 添加管理员账号
    users.approved.push({
      email: ADMIN_CONFIG.email,
      name: ADMIN_CONFIG.name,
      dept: ADMIN_CONFIG.dept,
      role: ADMIN_CONFIG.role,
      approvedTime: new Date().toISOString(),
      screenshot: null // 管理员不需要截图
    });

    saveUsers(users);
    console.log('✅ 管理员账号初始化成功');
    console.log('   邮箱:', ADMIN_CONFIG.email);
    console.log('   姓名:', ADMIN_CONFIG.name);
    console.log('   权限:', ADMIN_CONFIG.role);
  }

  // 设置当前登录用户
  function setCurrentUser() {
    const users = getUsers();
    const admin = users.approved.find(u => u.email === ADMIN_CONFIG.email);
    if (admin) {
      localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(admin));
      console.log('✅ 已自动登录管理员账号');
    }
  }

  // 执行初始化
  initAdmin();
  setCurrentUser();

  // 显示提示
  alert('管理员账号初始化完成！\n\n邮箱: ' + ADMIN_CONFIG.email + '\n姓名: ' + ADMIN_CONFIG.name + '\n权限: 管理员\n\n点击确定进入工作台');
  window.location.href = 'index.html';
})();
