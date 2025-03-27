"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const TopMenu = () => {
  const tabName = [
    // { name: "home", path: "/" },
    { name: "simulation", path: "/simulation" },
    { name: "parameter", path: "/parameter" },
  ];
  const pathname = usePathname();
  return (
    <nav className="shadow-md fixed top-0 left-0 right-0 bg-white z-50">
      <div role="tablist" className="tabs-boxed flex justify-center space-x-4">
        {tabName.map((item) => (
          <Link
            role="tab"
            aria-selected={pathname === item.path}
            aria-current={pathname === item.path ? "page" : undefined}
            key={item.name}
            href={item.path}
            className={
              pathname === item.path
                ? "tab tab-active px-4 text-lg"
                : "tab px-4 text-lg hover:bg-blue-200 transition-colors duration-500 ease-in-out"
            }
          >
            {item.name.charAt(0).toUpperCase() + item.name.slice(1)}
          </Link>
        ))}
      </div>
    </nav>
  );
};
export default TopMenu;
