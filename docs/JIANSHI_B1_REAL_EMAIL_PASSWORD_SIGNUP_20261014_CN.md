# 见势｜普通邮箱密码注册方案（2026-10-14）

本次将已存在的受控邮箱 Magic Link 扩展为**邮箱＋密码注册 / 登录 / 忘记密码邮件 / 修改密码**。注册调用 Supabase Auth 官方 signUp，登录调用 signInWithPassword，重置调用 resetPasswordForEmail，修改密码调用 updateUser。不另建用户密码表、不保存明文密码。原 Magic Link 保留为备选。

**当前能上线到用户侧了吗？不能。** 正式站 /account/ 仍会安全跳转；生产库只读检查证实 custom_smtp_configured、magic_link_e2e_pass、jwt_ab_isolation_pass 等八个 Auth Gate 均 false，account_auth 停用。仅将可实际接入 Supabase Auth 的功能代码与完整表单放入现有开启分支，不用假注册页面替代服务。

解锁实测还需要：Supabase 生产项目配置能发送注册确认与重置邮件的邮件服务，设置线上 Site URL / Redirect URLs；测试真实受控邮箱从注册、收信确认、登录、刷新、找回密码到退出；确认不同账户数据隔离及原八项验收；然后通过现有 Auth Gate 激活并重构 Pages。不可关闭邮箱确认/跳过数据隔离、不能将默认发信额度当成正式生产服务。

已完成的开发工作与已上线注册必须严格区分；当前 **未发送任何真实注册邮件，未创建真实用户，未修改生产 Auth 或数据库配置**。
