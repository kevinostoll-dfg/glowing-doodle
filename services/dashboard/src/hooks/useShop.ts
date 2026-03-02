import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";
import { createElement } from "react";
import { useQuery } from "@tanstack/react-query";
import { getShops } from "@/services/api";
import type { Shop, ShopContextState } from "@/types";

const ShopContext = createContext<ShopContextState | null>(null);

export function ShopProvider({ children }: { children: ReactNode }) {
  const [selectedShop, setSelectedShop] = useState<Shop | null>(null);

  return createElement(
    ShopContext.Provider,
    { value: { selectedShop, setSelectedShop } },
    children
  );
}

export function useShopContext(): ShopContextState {
  const context = useContext(ShopContext);
  if (!context) {
    throw new Error("useShopContext must be used within a ShopProvider");
  }
  return context;
}

export function useShops() {
  return useQuery({
    queryKey: ["shops"],
    queryFn: getShops,
    staleTime: 300_000,
  });
}

export { ShopContext };
