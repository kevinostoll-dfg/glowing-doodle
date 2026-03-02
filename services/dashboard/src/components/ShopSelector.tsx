import { useEffect, Fragment } from "react";
import { Listbox, Transition } from "@headlessui/react";
import { useShops, useShopContext } from "@/hooks/useShop";
import type { Shop } from "@/types";

export default function ShopSelector() {
  const { data: shops, isLoading } = useShops();
  const { selectedShop, setSelectedShop } = useShopContext();

  // Auto-select first shop when shops load and none is selected
  useEffect(() => {
    if (shops && shops.length > 0 && !selectedShop) {
      setSelectedShop(shops[0]);
    }
  }, [shops, selectedShop, setSelectedShop]);

  if (isLoading) {
    return (
      <div className="h-9 w-48 animate-pulse rounded-lg bg-surface-200" />
    );
  }

  if (!shops || shops.length === 0) {
    return (
      <span className="text-sm text-surface-500">No shops available</span>
    );
  }

  return (
    <Listbox value={selectedShop} onChange={setSelectedShop}>
      <div className="relative w-56">
        <Listbox.Button className="relative w-full cursor-pointer rounded-lg border border-surface-300 bg-white py-2 pl-3 pr-10 text-left text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">
          <span className="block truncate">
            {selectedShop?.name ?? "Select a shop"}
          </span>
          <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
            <svg
              className="h-5 w-5 text-surface-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 3a.75.75 0 01.55.24l3.25 3.5a.75.75 0 11-1.1 1.02L10 4.852 7.3 7.76a.75.75 0 01-1.1-1.02l3.25-3.5A.75.75 0 0110 3zm-3.76 9.2a.75.75 0 011.06.04l2.7 2.908 2.7-2.908a.75.75 0 111.1 1.02l-3.25 3.5a.75.75 0 01-1.1 0l-3.25-3.5a.75.75 0 01.04-1.06z"
                clipRule="evenodd"
              />
            </svg>
          </span>
        </Listbox.Button>

        <Transition
          as={Fragment}
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg bg-white py-1 text-sm shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
            {shops.map((shop: Shop) => (
              <Listbox.Option
                key={shop.id}
                value={shop}
                className={({ active }) =>
                  `relative cursor-pointer select-none py-2 pl-10 pr-4 ${
                    active ? "bg-brand-50 text-brand-700" : "text-surface-900"
                  }`
                }
              >
                {({ selected }) => (
                  <>
                    <span
                      className={`block truncate ${
                        selected ? "font-medium" : "font-normal"
                      }`}
                    >
                      {shop.name}
                    </span>
                    {selected && (
                      <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-brand-600">
                        <svg
                          className="h-5 w-5"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </span>
                    )}
                  </>
                )}
              </Listbox.Option>
            ))}
          </Listbox.Options>
        </Transition>
      </div>
    </Listbox>
  );
}
