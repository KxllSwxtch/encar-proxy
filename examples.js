useEffect(() => {
  const fetchManufacturers = async () => {
    setCurrentPage(1)
    const url = `https://encar-proxy.habsida.net/api/nav?count=true&q=(And.Hidden.N._.CarType.A._.SellType.%EC%9D%BC%EB%B0%98.)&inav=%7CMetadata%7CSort`

    const response = await axios.get(url)

    const data = response.data
    const count = data?.Count

    setTotalCars(count)

    const manufacturers =
      data?.iNav?.Nodes[1]?.Facets[0]?.Refinements?.Nodes[0]?.Facets

    setManufacturers(manufacturers)
  }

  fetchManufacturers()
}, [])

useEffect(() => {
  const fetchModelGroups = async () => {
    if (!selectedManufacturer) return

    setCurrentPage(1)

    const url = `https://encar-proxy.habsida.net/api/nav?count=true&q=(And.Hidden.N._.SellType.%EC%9D%BC%EB%B0%98._.(C.CarType.A._.Manufacturer.${selectedManufacturer}.))&inav=%7CMetadata%7CSort`

    try {
      const response = await axios.get(url)
      const data = response?.data
      const count = data?.Count

      setTotalCars(count)

      const allManufacturers =
        data?.iNav?.Nodes[2]?.Facets[0]?.Refinements?.Nodes[0]?.Facets

      const filteredManufacturer = allManufacturers.filter(
        (item) => item.IsSelected === true
      )[0]

      const models = filteredManufacturer?.Refinements?.Nodes[0]?.Facets

      setModelGroups(models)

      if (urlParams.current.modelGroup) {
        const modelExists = models?.some(
          (model) => model.Value === urlParams.current.modelGroup
        )
        if (modelExists) {
          setSelectedModelGroup(urlParams.current.modelGroup)
        }
      }
    } catch (error) {
      console.error("Ошибка при загрузке моделей:", error)
    }
  }

  fetchModelGroups()
}, [selectedManufacturer])

useEffect(() => {
  const fetchModelGroups = async () => {
    if (!selectedModelGroup) return
    setCurrentPage(1)

    const url = `https://encar-proxy.habsida.net/api/nav?count=true&q=(And.Hidden.N._.SellType.%EC%9D%BC%EB%B0%98._.(C.CarType.A._.(C.Manufacturer.${selectedManufacturer}._.ModelGroup.${selectedModelGroup}.)))&inav=%7CMetadata%7CSort`
    const response = await axios.get(url)

    const data = response?.data
    const count = data?.Count

    setTotalCars(count)

    const allManufacturers =
      data?.iNav?.Nodes[2]?.Facets[0]?.Refinements?.Nodes[0]?.Facets

    const filteredManufacturer = allManufacturers.filter(
      (item) => item.IsSelected === true
    )[0]

    const modelGroup = filteredManufacturer?.Refinements?.Nodes[0]?.Facets
    const filteredModel = modelGroup.filter(
      (item) => item.IsSelected === true
    )[0]
    const models = filteredModel?.Refinements?.Nodes[0]?.Facets

    setModels(models)

    if (urlParams.current.model) {
      const modelExists = models?.some(
        (model) => model.Value === urlParams.current.model
      )
      if (modelExists) {
        setSelectedModel(urlParams.current.model)
      }
      urlParams.current = {
        manufacturer: null,
        modelGroup: null,
        model: null,
      }
    }
  }

  fetchModelGroups()
}, [selectedManufacturer, selectedModelGroup])

useEffect(() => {
  const fetchConfigurations = async () => {
    if (!selectedModel) return
    setCurrentPage(1)

    const url = `https://encar-proxy.habsida.net/api/nav?count=true&q=(And.Hidden.N._.(C.CarType.A._.(C.Manufacturer.${selectedManufacturer}._.(C.ModelGroup.${selectedModelGroup}._.Model.${selectedModel}.))))&inav=%7CMetadata%7CSort`

    const response = await axios.get(url)

    const data = response?.data
    const count = data?.Count

    setTotalCars(count)

    const allManufacturers =
      data?.iNav?.Nodes[1]?.Facets[0]?.Refinements?.Nodes[0]?.Facets

    const filteredManufacturer = allManufacturers.filter(
      (item) => item.IsSelected === true
    )[0]

    const modelGroup = filteredManufacturer?.Refinements?.Nodes[0]?.Facets

    const filteredModel = modelGroup?.filter(
      (item) => item.IsSelected === true
    )[0]

    const models = filteredModel?.Refinements?.Nodes[0]?.Facets
    const filteredConfiguration = models?.filter(
      (item) => item.IsSelected === true
    )[0]

    const configurations = filteredConfiguration?.Refinements?.Nodes[0]?.Facets

    setConfigurations(configurations)
  }

  fetchConfigurations()
}, [selectedManufacturer, selectedModelGroup, selectedModel])

useEffect(() => {
  if (!selectedConfiguration) return
  setCurrentPage(1)

  const fetchBadges = async () => {
    const url = `https://encar-proxy.habsida.net/api/nav?count=true&q=(And.Hidden.N._.(C.CarType.A._.(C.Manufacturer.${selectedManufacturer}._.(C.ModelGroup.${selectedModelGroup}._.(C.Model.${selectedModel}._.BadgeGroup.${selectedConfiguration}.)))))&inav=%7CMetadata%7CSort`

    const response = await axios.get(url)

    const data = response?.data
    const count = data?.Count

    setTotalCars(count)

    const allManufacturers =
      data?.iNav?.Nodes[1]?.Facets[0]?.Refinements?.Nodes[0]?.Facets

    const filteredManufacturer = allManufacturers.filter(
      (item) => item.IsSelected === true
    )[0]

    const modelGroup = filteredManufacturer?.Refinements?.Nodes[0]?.Facets

    const filteredModel = modelGroup?.filter(
      (item) => item.IsSelected === true
    )[0]

    const models = filteredModel?.Refinements?.Nodes[0]?.Facets
    const filteredConfiguration = models?.filter(
      (item) => item.IsSelected === true
    )[0]

    const configurations = filteredConfiguration?.Refinements?.Nodes[0]?.Facets

    const filteredBadgeGroup = configurations?.filter(
      (item) => item.IsSelected === true
    )[0]

    const badges = filteredBadgeGroup?.Refinements?.Nodes[0]?.Facets

    setBadges(badges)
  }

  fetchBadges()
}, [
  selectedManufacturer,
  selectedModelGroup,
  selectedModel,
  selectedConfiguration,
  selectedBadge,
])

useEffect(() => {
  const fetchBadgeDetails = async () => {
    if (!selectedBadge) return
    setCurrentPage(1)

    const url = `https://encar-proxy.habsida.net/api/nav?count=true&q=(And.Hidden.N._.SellType.%EC%9D%BC%EB%B0%98._.(C.CarType.A._.(C.Manufacturer.${selectedManufacturer}._.(C.ModelGroup.${selectedModelGroup}._.(C.Model.${selectedModel}._.(C.BadgeGroup.${selectedConfiguration}._.Badge.${transformBadgeValue(
      selectedBadge
    )}.))))))&inav=%7CMetadata%7CSort`

    try {
      const response = await axios.get(url)

      const data = response?.data

      const count = data?.Count

      setTotalCars(count)

      const allManufacturers =
        data?.iNav?.Nodes[2]?.Facets[0]?.Refinements?.Nodes[0]?.Facets

      const filteredManufacturer = allManufacturers?.find(
        (item) => item.IsSelected
      )
      const modelGroup = filteredManufacturer?.Refinements?.Nodes[0]?.Facets
      const filteredModel = modelGroup?.find((item) => item.IsSelected)

      const models = filteredModel?.Refinements?.Nodes[0]?.Facets
      const filteredConfiguration = models?.find((item) => item.IsSelected)

      const configurations =
        filteredConfiguration?.Refinements?.Nodes[0]?.Facets
      const filteredBadgeGroup = configurations?.find((item) => item.IsSelected)

      const badges = filteredBadgeGroup?.Refinements?.Nodes[0]?.Facets
      const filteredBadge = badges?.find((item) => item.IsSelected)

      const badgeDetails = filteredBadge?.Refinements?.Nodes[0]?.Facets

      setBadgeDetails(badgeDetails)
    } catch (error) {
      console.error("Ошибка при получении badgeDetails:", error)
    }
  }

  fetchBadgeDetails()
}, [
  selectedManufacturer,
  selectedModelGroup,
  selectedModel,
  selectedConfiguration,
  selectedBadge,
])
