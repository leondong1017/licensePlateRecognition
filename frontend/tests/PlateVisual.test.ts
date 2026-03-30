import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PlateVisual from '../src/components/PlateVisual.vue'

describe('PlateVisual', () => {
  it('renders blue plate with correct CSS class', () => {
    const wrapper = mount(PlateVisual, {
      props: { province: '粤', cityCode: 'B', number: '88888', type: 'blue' }
    })
    expect(wrapper.find('.plate-root').classes()).toContain('plate-blue')
    expect(wrapper.text()).toContain('粤')
    expect(wrapper.text()).toContain('88888')
  })

  it('renders green plate for green_small type', () => {
    const wrapper = mount(PlateVisual, {
      props: { province: '京', cityCode: 'A', number: '12345D', type: 'green_small' }
    })
    expect(wrapper.find('.plate-root').classes()).toContain('plate-green')
  })

  it('renders yellow plate for yellow type', () => {
    const wrapper = mount(PlateVisual, {
      props: { province: '沪', cityCode: 'C', number: 'A6789', type: 'yellow' }
    })
    expect(wrapper.find('.plate-root').classes()).toContain('plate-yellow')
  })

  it('supports size prop sm', () => {
    const wrapper = mount(PlateVisual, {
      props: { province: '粤', cityCode: 'B', number: '88888', type: 'blue', size: 'sm' }
    })
    expect(wrapper.find('.plate-root').classes()).toContain('plate-sm')
  })
})
