# 准备
Ubuntu 22
```
sudo apt update -y
sudo apt full-upgrade -y
sudo apt install -y ack antlr3 asciidoc autoconf automake autopoint binutils bison build-essential \
bzip2 ccache cmake cpio curl device-tree-compiler fastjar flex gawk gettext gcc-multilib g++-multilib \
git gperf haveged help2man intltool libc6-dev-i386 libelf-dev libglib2.0-dev libgmp3-dev libltdl-dev \
libmpc-dev libmpfr-dev libncurses5-dev libncursesw5-dev libreadline-dev libssl-dev libtool lrzsz \
mkisofs msmtp nano ninja-build p7zip p7zip-full patch pkgconf python2.7 python3 python3-pyelftools \
libpython3-dev qemu-utils rsync scons squashfs-tools subversion swig texinfo uglifyjs upx-ucl unzip \vim wget xmlto xxd zlib1g-dev
```
# LEDE添加包
需要添加UA2F模块和RKP-IPID模块
- [https://github.com/Zxilly/UA2F](https://github.com/Zxilly/UA2F)
- [https://github.com/CHN-beta/rkp-ipid](https://github.com/CHN-beta/rkp-ipid)

命令行如下
```
cd lede
git clone https://github.com/Zxilly/UA2F.git package/UA2F
git clone https://github.com/CHN-beta/rkp-ipid.git package/rkp-ipid
```
# LEDE添加其他包
添加下面代码复制到 lede源码根目录 feeds.conf.default 文件
```
src-git kenzo https://github.com/kenzok8/openwrt-packages
src-git small https://github.com/kenzok8/small
```
# 更新feed模块
```
./scripts/feeds update -a
./scripts/feeds install -a
```
# 打开编译菜单
```
make menuconfig
```
# LEDE编译选择

勾选 ipid 模块
```
kernel-modules->Other modules->kmod-rkp-ipid
```
选上模块
```
kernel modules->Netfilter Extensions->kmod-ipt-u32
kernel modules->Netfilter Extensions->kmod-ipt-ipopt
```
勾选ua2f模块
```
network->Routing and Redirection->ua2f
network->firewall->iptables-mod-filter
network->firewall->iptables-mod-ipopt
network->firewall->iptables-mod-u32
network->firewall->iptables-mod-conntrack-extra
```

# 防检测配置
原文参考： https://blog.sunbk201.site/posts/crack-campus-network
## 时钟设置
进入 OpenWrt 系统设置, 启用 NTP 客户端 和 作为 NTP 服务器提供服务

NTP server candidates（候选 NTP 服务器）四个框框分别填写:
```
ntp1.aliyun.com
time1.cloud.tencent.com
stdtime.gov.hk
pool.ntp.org
```
## 防火墙配置
下面的全部代码块内容可直接粘贴进防火墙的自定义规则中，
```
# @SunBK201 - https://blog.sunbk201.site
iptables -t nat -A PREROUTING -p udp --dport 53 -j REDIRECT --to-ports 53
iptables -t nat -A PREROUTING -p tcp --dport 53 -j REDIRECT --to-ports 53

# 通过 rkp-ipid 设置 IPID
iptables -t mangle -N IPID_MOD
iptables -t mangle -A FORWARD -j IPID_MOD
iptables -t mangle -A OUTPUT -j IPID_MOD
iptables -t mangle -A IPID_MOD -d 0.0.0.0/8 -j RETURN
iptables -t mangle -A IPID_MOD -d 127.0.0.0/8 -j RETURN
# 下面需要根据你的校园网情况确定是否需要注释掉部分内容，一般不用修改
iptables -t mangle -A IPID_MOD -d 10.0.0.0/8 -j RETURN
iptables -t mangle -A IPID_MOD -d 172.16.0.0/12 -j RETURN
iptables -t mangle -A IPID_MOD -d 192.168.0.0/16 -j RETURN
iptables -t mangle -A IPID_MOD -d 255.0.0.0/8 -j RETURN
iptables -t mangle -A IPID_MOD -j MARK --set-xmark 0x10/0x10

# ua2f 改UA
iptables -t mangle -N ua2f
# 下面需要根据你的校园网情况确定是否需要注释掉部分内容，一般不用修改
iptables -t mangle -A ua2f -d 10.0.0.0/8 -j RETURN
iptables -t mangle -A ua2f -d 127.0.0.0/8 -j RETURN
iptables -t mangle -A ua2f -d 192.168.0.0/16 -j RETURN # 不处理流向保留地址的包
iptables -t mangle -A ua2f -p tcp --dport 443 -j RETURN # 不处理 https
iptables -t mangle -A ua2f -p tcp --dport 22 -j RETURN # 不处理 SSH 
iptables -t mangle -A ua2f -p tcp --dport 80 -j CONNMARK --set-mark 44
iptables -t mangle -A ua2f -m connmark --mark 43 -j RETURN # 不处理标记为非 http 的流 (实验性)
iptables -t mangle -A ua2f -m set --set nohttp dst,dst -j RETURN
iptables -t mangle -A ua2f -j NFQUEUE --queue-num 10010
  
iptables -t mangle -A FORWARD -p tcp -m conntrack --ctdir ORIGINAL -j ua2f
iptables -t mangle -A FORWARD -p tcp -m conntrack --ctdir REPLY


# 防时钟偏移检测
iptables -t nat -N ntp_force_local
iptables -t nat -I PREROUTING -p udp --dport 123 -j ntp_force_local
iptables -t nat -A ntp_force_local -d 0.0.0.0/8 -j RETURN
iptables -t nat -A ntp_force_local -d 127.0.0.0/8 -j RETURN
iptables -t nat -A ntp_force_local -d 192.168.0.0/16 -j RETURN
# 这一条最后的 192.168.1.1 需要根据你路由器的网关进行修改，如果你修改了默认网关，那么这里也需要修改成你的默认网关
iptables -t nat -A ntp_force_local -s 192.168.0.0/16 -j DNAT --to-destination 192.168.1.1

# 通过 iptables 修改 TTL 值
iptables -t mangle -A POSTROUTING -j TTL --ttl-set 64

# iptables 拒绝 AC 进行 Flash 检测
iptables -I FORWARD -p tcp --sport 80 --tcp-flags ACK ACK -m string --algo bm --string " src=\"http://1.1.1." -j DROP  
```
# 防火墙SSH配置
此处的内容需要你进入SSH来执行以下命令
```
# 开机自启
uci set ua2f.enabled.enabled=1
# 自动配置防火墙（默认开启）（建议开启）
uci set ua2f.firewall.handle_fw=1
uci set ua2f.firewall.handle_tls=1
uci set ua2f.firewall.handle_mmtls=1
uci set ua2f.firewall.handle_intranet=1
# 保存配置
uci commit ua2f

操作：# 开机自启
service ua2f enable
# 启动ua2f
service ua2f start

# 手动关闭ua2f（这是关闭！！！别无脑粘贴！！！）
service ua2f stop
```
