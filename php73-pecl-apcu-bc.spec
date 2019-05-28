# IUS spec file for php73-pecl-apcu-bc, forked from:
#
# Fedora spec file for php-pecl-apcu-bc
# without SCL compatibility, from
#
# remirepo spec file for php-pecl-apcu-bc
#
# Copyright (c) 2015-2019 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/4.0/
#
# Please, preserve the changelog entries
#

# we don't want -z defs linker flag
%undefine _strict_symbol_defs_build

%global proj_name  apcu_bc
%global pecl_name  apcu-bc
%global ext_name   apc
%global apcver     %(%{_bindir}/php -r 'echo (phpversion("apcu")?:0);' 2>/dev/null || echo 65536)
%global with_zts   0%{!?_without_zts:%{?__ztsphp:1}}
# After 40-apcu.ini
%global ini_name   50-%{ext_name}.ini
%global php        php73

Name:           %{php}-pecl-%{pecl_name}
Summary:        APCu Backwards Compatibility Module
Version:        1.0.5
Release:        2%{?dist}
Source0:        https://pecl.php.net/get/%{proj_name}-%{version}.tgz

License:        PHP
URL:            https://pecl.php.net/package/APCu

BuildRequires:  gcc
BuildRequires:  %{php}-devel
# build require pear1's dependencies to avoid mismatched php stacks
BuildRequires:  pear1 %{php}-cli %{php}-common %{php}-xml
BuildRequires:  %{php}-pecl-apcu-devel >= 5.1.2

Requires:       php(zend-abi) = %{php_zend_api}
Requires:       php(api) = %{php_core_api}
Requires:       %{php}-pecl-apcu%{?_isa} >= 5.1.2

Provides:       php-apc                   = %{apcver}
Provides:       php-apc%{?_isa}           = %{apcver}
Provides:       php-pecl-apc              = %{apcver}-%{release}
Provides:       php-pecl-apc%{?_isa}      = %{apcver}-%{release}
Provides:       php-pecl(APC)             = %{apcver}
Provides:       php-pecl(APC)%{?_isa}     = %{apcver}
Provides:       php-pecl(%{proj_name})         = %{version}
Provides:       php-pecl(%{proj_name})%{?_isa} = %{version}

# safe replacement
Provides:       php-pecl-%{pecl_name} = %{version}-%{release}
Provides:       php-pecl-%{pecl_name}%{?_isa} = %{version}-%{release}
Conflicts:      php-pecl-%{pecl_name} < %{version}-%{release}


%description
This module provides a backwards compatible API for APC.


%prep
%setup -qc
mv %{proj_name}-%{version} NTS

# Don't install/register tests
sed -e 's/role="test"/role="src"/' \
    -e '/LICENSE/s/role="doc"/role="src"/' \
    -i package.xml

cd NTS
# Sanity check, really often broken
extver=$(sed -n '/#define PHP_APCU_BC_VERSION/{s/.* "//;s/".*$//;p}' php_apc.h)
if test "x${extver}" != "x%{version}%{?prever}%{?gh_date:dev}"; then
   : Error: Upstream extension version is ${extver}, expecting %{version}%{?prever}%{?gh_date:dev}.
   exit 1
fi
cd ..

%if %{with_zts}
# duplicate for ZTS build
cp -pr NTS ZTS
%endif

cat << 'EOF' | tee %{ini_name}
; Enable %{summary}
extension=%{ext_name}.so
EOF

: Build apcu_bc %{version} with apcu %{apcver}


%build
cd NTS
%{_bindir}/phpize
%configure \
   --enable-apcu-bc \
   --with-php-config=%{_bindir}/php-config
%make_build

%if %{with_zts}
cd ../ZTS
%{_bindir}/zts-phpize
%configure \
   --enable-apcu-bc \
   --with-php-config=%{_bindir}/zts-php-config
%make_build
%endif


%install
# Install the NTS stuff
make -C NTS install INSTALL_ROOT=%{buildroot}
install -D -m 644 %{ini_name} %{buildroot}%{php_inidir}/%{ini_name}

%if %{with_zts}
# Install the ZTS stuff
make -C ZTS install INSTALL_ROOT=%{buildroot}
install -D -m 644 %{ini_name} %{buildroot}%{php_ztsinidir}/%{ini_name}
%endif

# Install the package XML file
install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{proj_name}.xml

# Documentation
for i in $(grep 'role="doc"' package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 NTS/$i %{buildroot}%{pecl_docdir}/%{proj_name}/$i
done


%check
cd NTS
# Check than both extensions are reported (BC mode)
%{__php} -n \
   -d extension=apcu.so \
   -d extension=%{buildroot}%{php_extdir}/apc.so \
   -m | grep 'apc$'

# Upstream test suite for NTS extension
TEST_PHP_EXECUTABLE=%{__php} \
TEST_PHP_ARGS="-n -d extension=apcu.so -d extension=%{buildroot}%{php_extdir}/apc.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__php} -n run-tests.php --show-diff

%if %{with_zts}
cd ../ZTS
%{__ztsphp} -n \
   -d extension=apcu.so \
   -d extension=%{buildroot}%{php_ztsextdir}/apc.so \
   -m | grep 'apc$'

# Upstream test suite for ZTS extension
TEST_PHP_EXECUTABLE=%{__ztsphp} \
TEST_PHP_ARGS="-n -d extension=apcu.so -d extension=%{buildroot}%{php_ztsextdir}/apc.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__ztsphp} -n run-tests.php --show-diff
%endif


%triggerin -- pear1
if [ -x %{__pecl} ]; then
    %{pecl_install} %{pecl_xmldir}/%{proj_name}.xml >/dev/null || :
fi


%posttrans
if [ -x %{__pecl} ]; then
    %{pecl_install} %{pecl_xmldir}/%{proj_name}.xml >/dev/null || :
fi


%postun
if [ $1 -eq 0 -a -x %{__pecl} ]; then
    %{pecl_uninstall} %{proj_name} >/dev/null || :
fi


%files
%license NTS/LICENSE
%doc %{pecl_docdir}/%{proj_name}
%{pecl_xmldir}/%{proj_name}.xml

%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/apc.so

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/%{ini_name}
%{php_ztsextdir}/apc.so
%endif


%changelog
* Tue May 28 2019 Carl George <carl@george.computer> - 1.0.5-2
- Port from Fedora to IUS

* Wed Feb 20 2019 Remi Collet <remi@remirepo.net> - 1.0.5-1
- update to 1.0.5

* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.4-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Thu Oct 11 2018 Remi Collet <remi@remirepo.net> - 1.0.4-3
- Rebuild for https://fedoraproject.org/wiki/Changes/php73

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Fri Feb 16 2018 Remi Collet <remi@remirepo.net> - 1.0.4-1
- update to 1.0.4 (stable, no change)

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.3-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Jan 26 2018 Remi Collet <remi@remirepo.net> - 1.0.3-9
- undefine _strict_symbol_defs_build

* Tue Oct 03 2017 Remi Collet <remi@fedoraproject.org> - 1.0.3-8
- rebuild for https://fedoraproject.org/wiki/Changes/php72

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.3-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.3-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.3-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Nov 14 2016 Remi Collet <remi@fedoraproject.org> - 1.0.3-4
- rebuild for https://fedoraproject.org/wiki/Changes/php71

* Sun Jun 26 2016 Remi Collet <remi@fedoraproject.org> - 1.0.3-3
- drop SCL stuff for Fedora review

* Mon Mar  7 2016 Remi Collet <remi@fedoraproject.org> - 1.0.3-2
- fix apcver macro definition

* Thu Feb 11 2016 Remi Collet <remi@fedoraproject.org> - 1.0.3-1
- Update to 1.0.3 (beta)

* Fri Jan 29 2016 Remi Collet <remi@fedoraproject.org> - 1.0.2-1
- Update to 1.0.2 (beta)

* Wed Jan  6 2016 Remi Collet <remi@fedoraproject.org> - 1.0.1-1
- Update to 1.0.1 (beta)

* Mon Jan  4 2016 Remi Collet <remi@fedoraproject.org> - 1.0.1-0
- test build for upcoming 1.0.1

* Sat Dec 26 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-2
- missing dependency on APCu

* Mon Dec  7 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-1
- Update to 1.0.0 (beta)

* Mon Dec  7 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-0.2
- test build of upcomming 1.0.0

* Fri Dec  4 2015 Remi Collet <remi@fedoraproject.org> - 5.1.2-0.1.20151204git52b97a7
- test build of upcomming 5.1.2
- initial package
