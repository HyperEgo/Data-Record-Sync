find ./ -name "*.rpm" -exec mv '{}' /data_local/repo/IBCS-other/. \;
cd /data_local/repo/IBCS-other/
createrepo .
sed -i 's/enabled = 0/enabled = 1/' /etc/yum.repos.d/IBCS-other.repo
yum repolist
yum clean all
yum makecache
yum install git vlc python3 tkinter
sed -i 's/enabled = 1/enabled = 0/' /etc/yum.repos.d/IBCS-other.repo
yum repolist &> /dev/null
