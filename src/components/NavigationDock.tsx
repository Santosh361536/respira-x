import { HomeIcon, Sparkles, Users, Moon, Sun } from 'lucide-react';
import { Dock, DockIcon, DockItem, DockLabel } from '@/components/ui/dock';
import { useEffect, useState } from 'react';

function NavigationDock() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    setIsDark(root.classList.contains('dark'));
  }, []);

  const toggleTheme = () => {
    const root = document.documentElement;
    root.classList.toggle('dark');
    setIsDark(!isDark);
  };

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  const navItems = [
    {
      title: 'Home',
      icon: <HomeIcon className="h-full w-full text-foreground" />,
      onClick: () => scrollTo('hero'),
    },
    {
      title: 'Features',
      icon: <Sparkles className="h-full w-full text-foreground" />,
      onClick: () => scrollTo('features'),
    },
    {
      title: 'About Us',
      icon: <Users className="h-full w-full text-foreground" />,
      onClick: () => scrollTo('about'),
    },
    {
      title: isDark ? 'Light Mode' : 'Dark Mode',
      icon: isDark
        ? <Sun className="h-full w-full text-foreground" />
        : <Moon className="h-full w-full text-foreground" />,
      onClick: toggleTheme,
    },
  ];

  return (
    <div className="z-50">
      <Dock magnification={70} distance={120} panelHeight={56}>
        {navItems.map((item) => (
          <DockItem key={item.title}>
            <DockLabel>{item.title}</DockLabel>
            <DockIcon>
              <button
                onClick={item.onClick}
                className="h-full w-full flex items-center justify-center"
                aria-label={item.title}
              >
                {item.icon}
              </button>
            </DockIcon>
          </DockItem>
        ))}
      </Dock>
    </div>
  );
}

export default NavigationDock;
